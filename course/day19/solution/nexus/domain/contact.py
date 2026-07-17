"""企业协作者领域对象。"""


class Contact:
    """企业协作者领域对象。"""

    def __init__(self, contact_id, name, department, role, email, skills=None):
        self.contact_id = contact_id.strip().upper().replace(" ", "")
        self.name = " ".join(name.split())
        self.department = department
        self.role = " ".join(role.split())
        self.email = email.strip().lower()
        self.skills = self.normalize_skills(skills or [])

    def to_dict(self):
        return {
            "contact_id": self.contact_id,
            "name": self.name,
            "department": self.department,
            "role": self.role,
            "email": self.email,
            "skills": self.skills,
        }

    def matches(self, keyword):
        query = keyword.strip().lower()
        if query == "":
            return False
        searchable = " ".join(
            [
                self.name,
                self.department,
                self.role,
                self.email,
                " ".join(self.skills),
            ]
        ).lower()
        return query in searchable

    def update_role(self, new_role):
        normalized = " ".join(new_role.split())
        if normalized == "" or normalized == self.role:
            return False
        self.role = normalized
        return True

    @classmethod
    def from_dict(cls, data):
        return cls(
            data["contact_id"],
            data["name"],
            data["department"],
            data["role"],
            data["email"],
            data.get("skills", []),
        )

    @staticmethod
    def normalize_skills(skills):
        return sorted(
            {skill.strip().lower() for skill in skills if skill.strip()}
        )

    @staticmethod
    def is_valid_email(email):
        value = email.strip().lower()
        if value.count("@") != 1:
            return False
        local_part, domain = value.split("@")
        return (
            local_part != ""
            and domain != ""
            and "." in domain
            and domain[0:1] != "."
            and domain[-1:] != "."
        )
