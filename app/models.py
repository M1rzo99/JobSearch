from dataclasses import dataclass, field


@dataclass
class Job:
    source: str          # "wanted" | "saramin" | "jobkorea"
    source_id: str
    url: str
    title: str
    company: str
    location: str = ""
    salary: str = ""
    deadline: str = ""
    job_type: str = ""
    career: str = ""
    description: str = ""
    apply_email: str = ""
    tags: list[str] = field(default_factory=list)
    score: int = 0
    matched: list[str] = field(default_factory=list)

    @property
    def uid(self) -> str:
        return f"{self.source}:{self.source_id}"
