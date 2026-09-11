from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
from ..mailing.service import prepare_post, send_book

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

        report = send_book(
            author_name=author_name,
            book_title=book_title,
            age_rating=age_rating,
            annotation=annotation,
            book_links=book_links,
            token=token,
            day=day,
            attachment=attachment.strip() or None,
        )
        ctx["report_path"] = str(report)
    except Exception as exc:
        ctx["error"] = str(exc)
    return templates.TemplateResponse(request, "campaign.html", ctx)