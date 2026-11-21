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
    assert j.score >= 10 and "우즈베크" in j.matched
    assert score_job(Job("x","2","u","일본어 통역","A"), p).score == -1

def test_card_html():
    j = Job("saramin","1","https://x","통역 <A&B>","회사", location="서울", description="a<b>", score=12, matched=["통역"])
    t = job_text(j)
    assert "&lt;A&amp;B&gt;" in t and "<blockquote expandable>" in t
    assert len(job_keyboard(j.uid, j.url).inline_keyboard[0][0].callback_data.encode()) <= 64

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
