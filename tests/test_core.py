import asyncio
from app.dedup import dedup_key, is_similar
from app.db import DB
from app.matcher import score_job
from app.models import Job
from app.cards import job_text, job_keyboard
from app.sources import saramin
from app.config import load_profile

def test_dedup_cross_platform(tmp_path):
    db = DB(tmp_path / "t.db")
    a = Job("saramin", "1", "u", "[정규직] 우즈베크어 통역 담당자 채용", "(주)한우무역")
    b = Job("jobkorea", "9", "u", "우즈베크어 통역 담당자 모집", "주식회사 한우무역")
    c = Job("wanted", "5", "u", "우즈베크어 통번역 담당", "한우무역 Co., Ltd.")
    db.add(a, "sent")
    assert db.find_duplicate(b) is not None
    assert db.find_duplicate(c) is not None
    d = Job("wanted", "6", "u", "백엔드 개발자", "한우무역")
    assert db.find_duplicate(d) is None

def test_score():
    p = load_profile()
    j = score_job(Job("x","1","u","우즈베크어 통역사 채용","A", description="타슈켄트 출장"), p)
    assert j.score >= 10 and j.matched[0] == "Tarjima"
    assert score_job(Job("x","2","u","일본어 통역","A"), p).score == -1

def test_categories_filter():
    p = load_profile()
    ok = lambda t, d="": score_job(Job("x","1","u",t,"A", description=d), p).score > 0
    assert ok("한-우즈베크 무역회사 사무직", "타슈켄트 지사")          # Hamkorlik
    assert ok("백엔드 개발자 (Python)")                                # IT
    assert ok("Frontend Developer")                                    # IT
    assert not ok("해외영업 담당 (우즈베키스탄)")                       # 영업 chiqarib tashlanadi
    assert not ok("영어 통역사")                                       # o'zbekchasiz tarjima emas
    assert not ok("물류센터 사무직", "We work with partners")          # 'IT' so'z ichida emas
    assert not ok("회계 담당자")

def test_card_html():
    j = Job("saramin","1","https://x","통역 <A&B>","회사", location="서울", description="a<b>", score=12, matched=["통역"])
    t = job_text(j)
    assert "&lt;A&amp;B&gt;" in t and "<blockquote expandable>" in t
    kb = job_keyboard(j.uid, j.url).inline_keyboard
    assert len(kb) == 1 and kb[0][0].callback_data.startswith("rej|") and kb[0][1].url == "https://x"
    assert len(kb[0][0].callback_data.encode()) <= 64

def test_saramin_html(monkeypatch):
    html = '''<div class="item_recruit" value="555"><h2 class="job_tit"><a href="/zf_user/jobs/relay/view?rec_idx=555" title="우즈베크어 통역">x</a></h2>
    <strong class="corp_name"><a>(주)테스트</a></strong><div class="job_condition"><span>서울 강남구</span><span>신입</span><span>학력무관</span><span>정규직</span></div>
    <div class="job_date"><span class="date">~ 12/31(수)</span></div></div>'''
    class R: text = html
    class C:
        async def get(self, *a, **k): return R()
    jobs = asyncio.run(saramin._search_html(C(), "q"))
    assert jobs[0].source_id == "555" and jobs[0].company == "(주)테스트" and jobs[0].job_type == "정규직"

def test_accepted_keyboard_points_to_platform():
    from app.cards import accepted_keyboard
    kb = accepted_keyboard("https://www.saramin.co.kr/zf_user/jobs/relay/view?rec_idx=1", "saramin")
    b = kb.inline_keyboard[0][0]
    assert "즉시지원" in b.text and b.url.startswith("https://www.saramin.co.kr")

def test_webhook_accept_shifts_entities():
    from datetime import datetime
    from api.telegram import accepted_edit, utf16_len, webhook_secret
    from app.run_once import webhook_secret as ws2
    assert webhook_secret("t") == ws2("t")
    msg = {"chat": {"id": 1}, "message_id": 2, "text": "🏢 통역 직무",
           "entities": [{"type": "bold", "offset": 3, "length": 2}],
           "reply_markup": {"inline_keyboard": [[{"text": "a", "callback_data": "acc|saramin:1"}], [{"text": "o", "url": "https://s/1"}]]}}
    out = accepted_edit(msg, "saramin", datetime(2026, 11, 21, 12, 0))
    prefix = out["text"][: out["text"].index("🏢")]
    assert out["entities"][1]["offset"] == 3 + utf16_len(prefix)
    t = out["text"]; e = out["entities"][1]
    assert t.encode("utf-16-le")[2*e["offset"]:2*(e["offset"]+e["length"])].decode("utf-16-le") == "통역"
    assert out["reply_markup"]["inline_keyboard"][0][0]["url"] == "https://s/1"
    assert "즉시지원" in out["reply_markup"]["inline_keyboard"][0][0]["text"]


def test_clean_token():
    from app.config import clean_token
    tok = "123456789:AAHabcdefghijklmnopqrstuvwxyz012345"
    assert clean_token(f"  {tok}\n") == tok
    assert clean_token(f'"bot{tok}"') == tok


def test_profile_filters():
    from app.matcher import max_salary_manwon
    p = load_profile()
    mk = lambda **k: score_job(Job("x","1","u", k.pop("title", "백엔드 개발자"), "A", **k), p).score > 0
    assert mk(location="서울 강남구") and mk(location="경기 성남시") and mk(location="대전 유성구")
    assert mk(location="")                                  # hudud yozilmagan -> o'tadi
    assert not mk(location="부산 해운대구")
    assert not mk(job_type="계약직")
    assert mk(job_type="정규직, 계약직")
    assert not mk(title="QA 인턴")
    assert mk(title="IT PM (우즈베키스탄 프로젝트)")
    assert not mk(salary="2,800~3,000만원")
    assert mk(salary="3,000~4,000만원") and mk(salary="면접 후 결정")
    assert max_salary_manwon("월 250만원") == 3000
    assert max_salary_manwon("연봉 35,000,000원") == 3500
    assert max_salary_manwon("회사내규에 따름") is None


def test_cv_filters():
    from app.matcher import min_required_years
    p = load_profile()
    sc = lambda **k: score_job(Job("x","1","u", k.pop("title", "프론트엔드 개발자 (React)"), "A", **k), p).score
    assert sc() > sc(title="QA 엔지니어")                       # CV texnologiyalari yuqoriroq
    assert sc(title="시니어 프론트엔드 개발자") < 0
    assert sc(career="경력 7년 이상") < 0
    assert sc(career="경력 2~4년") > 0 and sc(career="신입·경력") > 0
    assert sc(description="내국인만 지원 가능") < 0
    assert sc(description="외국인 가능, 비자 지원") > sc()
    assert min_required_years("경력 3~5년") == 3 and min_required_years("경력무관") is None
