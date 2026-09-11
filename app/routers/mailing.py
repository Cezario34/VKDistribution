from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from ..mailing.service import prepare_post
from ..mailing.jobs import start_mailing_job, get_job

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

DAY_CHOICES = [
    (0, "Тестовый файл"),
    (1, "День 1"),
    (2, "День 2"),
    (3, "День 3"),
    (4, "День 4"),
    (5, "День 5"),
    (6, "День 6"),
    (7, "День 7"),
    (8, "День 8"),
    (9, "День 9"),
    (10, "СЛР"),
    (50, "СЛР 2"),
]


@router.get("/send")
def send_form(request: Request):
    return templates.TemplateResponse(request, "campaign.html", {
        "user": None,
        "step": 3,
        "days": DAY_CHOICES,
        "error": None,
        "preview": None,
        "report_path": None,
        "values": {},
    })


@router.post("/send")
def send_submit(
    request: Request,
    author_name: str = Form(...),
    book_title: str = Form(...),
    age_rating: str = Form(...),
    annotation: str = Form(...),
    book_links: str = Form(...),
    token: str = Form(...),
    day: int = Form(...),
    attachment: str = Form(""),
    action: str = Form("send"),
):
    values = {
        "author_name": author_name,
        "book_title": book_title,
        "age_rating": age_rating,
        "annotation": annotation,
        "book_links": book_links,
        "attachment": attachment,
        "day": day,
    }
    ctx = {
        "user": None,
        "step": 3,
        "days": DAY_CHOICES,
        "error": None,
        "preview": None,
        "report_path": None,
        "values": values,
    }
    try:
        text = prepare_post(
            author_name=author_name,
            book_title=book_title,
            age_rating=age_rating,
            annotation=annotation,
            book_links=book_links,
        )
        ctx["preview"] = text
        if action == "preview":
            return templates.TemplateResponse(request, "campaign.html", ctx)

        job_id = start_mailing_job(
            author_name=author_name,
            book_title=book_title,
            age_rating=age_rating,
            annotation=annotation,
            book_links=book_links,
            token=token,
            day=day,
            attachment=attachment.strip() or None,
        )
        return RedirectResponse(f"/send/progress/{job_id}", status_code=303)
    except Exception as exc:
        ctx["error"] = str(exc)
        return templates.TemplateResponse(request, "campaign.html", ctx)



@router.get("/send/progress/{job_id}")
def send_progress(request: Request, job_id: str):
    if not get_job(job_id):
        return HTMLResponse("Задача не найдена", status_code=404)
    return templates.TemplateResponse(request, "progress.html", {"job_id": job_id})


@router.get("/send/status/{job_id}")
def send_status(job_id: str):
    job = get_job(job_id)
    if not job:
        return {"ok": 0, "err": 0, "processed": 0, "total": 0, "done": True, "failed": True, "message": "Задача не найдена", "current": ""}
    return job

@router.get("/send/report/{job_id}")
def send_report(job_id: str):
    job = get_job(job_id)
    if not job or not job.get("report_name"):
        return HTMLResponse("Отчёт ещё не готов", status_code=404)
    path = Path("group_target") / job["report_name"]
    if not path.exists():
        return HTMLResponse("Файл отчёта не найден", status_code=404)
    return FileResponse(
        path,
        filename=job["report_name"],
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )