from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.models.legal_knowledge import Law, LawSection

VERIFIED_BANGLADESH_STATUTES = [
    {
        "act_name": "The Transfer of Property Act",
        "act_year": 1882,
        "act_number": "Act IV of 1882",
        "category": "property",
        "sections": [
            {
                "section_number": "105",
                "title": "Lease defined",
                "content": "A lease of immoveable property is a transfer of a right to enjoy such property, made for a certain time, express or implied, or in perpetuity, in consideration of a price paid or promised, or of money, a share of crops, service or any other thing of value, to be rendered periodically or on specified occasions to the transferor by the transferee, who accepts the transfer on such terms.",
                "source_url": "http://bdlaws.minlaw.gov.bd/act-48/section-3157.html"
            },
            {
                "section_number": "106",
                "title": "Duration of certain leases in absence of written contract or local usage",
                "content": "In the absence of a contract or local law or usage to the contrary, a lease of immoveable property for agricultural or manufacturing purposes shall be deemed to be a lease from year to year, terminable, on the part of either lessor or lessee, by six months' notice; and a lease of immoveable property for any other purpose shall be deemed to be a lease from month to month, terminable, on the part of either lessor or lessee, by fifteen days' notice.",
                "source_url": "http://bdlaws.minlaw.gov.bd/act-48/section-3158.html"
            },
            {
                "section_number": "107",
                "title": "Leases how made",
                "content": "A lease of immoveable property from year to year, or for any term exceeding one year, or reserving a yearly rent, can be made only by a registered instrument. All other leases of immoveable property may be made either by a registered instrument or by oral agreement accompanied by delivery of possession.",
                "source_url": "http://bdlaws.minlaw.gov.bd/act-48/section-3159.html"
            },
            {
                "section_number": "108",
                "title": "Rights and liabilities of lessor and lessee",
                "content": "In the absence of a contract or local usage to the contrary, the lessor and the lessee of immoveable property, as against one another, respectively, possess the rights and are subject to the liabilities specified in the rules set forth in this section.",
                "source_url": "http://bdlaws.minlaw.gov.bd/act-48/section-3160.html"
            }
        ]
    },
    {
        "act_name": "The Registration Act",
        "act_year": 1908,
        "act_number": "Act XVI of 1908",
        "category": "registration",
        "sections": [
            {
                "section_number": "17",
                "title": "Documents of which registration is compulsory",
                "content": "Leases of immovable property from year to year, or for any term exceeding one year, or reserving a yearly rent, must be compulsorily registered.",
                "source_url": "http://bdlaws.minlaw.gov.bd/act-93/section-3580.html"
            },
            {
                "section_number": "49",
                "title": "Effect of non-registration of documents required to be registered",
                "content": "No document required by section 17 or by any provision of the Transfer of Property Act, 1882 to be registered shall affect any immovable property comprised therein unless it has been registered.",
                "source_url": "http://bdlaws.minlaw.gov.bd/act-93/section-3612.html"
            }
        ]
    },
    {
        "act_name": "The Stamp Act",
        "act_year": 1899,
        "act_number": "Act II of 1899",
        "category": "revenue",
        "sections": [
            {
                "section_number": "Schedule I, Article 35",
                "title": "Stamp duty on Leases",
                "content": "Prescribes ad valorem or fixed non-judicial stamp duty payable depending on lease term, advance consideration, and average annual rent in Bangladesh.",
                "source_url": "http://bdlaws.minlaw.gov.bd/act-78.html"
            }
        ]
    },
    {
        "act_name": "The Contract Act",
        "act_year": 1872,
        "act_number": "Act IX of 1872",
        "category": "contract",
        "sections": [
            {
                "section_number": "10",
                "title": "What agreements are contracts",
                "content": "All agreements are contracts if they are made by the free consent of parties competent to contract, for a lawful consideration and with a lawful object, and are not hereby expressly declared to be void.",
                "source_url": "http://bdlaws.minlaw.gov.bd/act-26/section-2200.html"
            },
            {
                "section_number": "73",
                "title": "Compensation for loss or damage caused by breach of contract",
                "content": "When a contract has been broken, the party who suffers by such breach is entitled to receive from the party who has broken the contract, compensation for any loss or damage caused to him thereby.",
                "source_url": "http://bdlaws.minlaw.gov.bd/act-26/section-2263.html"
            }
        ]
    }
]

class KnowledgeService:
    @staticmethod
    def seed_initial_statutes(db: Session):
        """Seed verified Bangladesh statutes into database if not already present."""
        for statute_data in VERIFIED_BANGLADESH_STATUTES:
            existing_law = db.query(Law).filter(Law.act_name == statute_data["act_name"]).first()
            if not existing_law:
                law = Law(
                    act_name=statute_data["act_name"],
                    act_year=statute_data["act_year"],
                    act_number=statute_data["act_number"],
                    category=statute_data["category"],
                    status="in_force"
                )
                db.add(law)
                db.flush()

                for sec_data in statute_data["sections"]:
                    sec = LawSection(
                        law_id=law.id,
                        section_number=sec_data["section_number"],
                        title=sec_data["title"],
                        content=sec_data["content"],
                        source_url=sec_data["source_url"],
                        verified_status="verified"
                    )
                    db.add(sec)
        db.commit()

    @staticmethod
    def verify_statutory_reference(act_name_substr: str, section_num: str, db: Session) -> Dict[str, Any]:
        """
        Anti-Hallucination Guardrail:
        Checks if a cited section exists in the verified knowledge base.
        """
        query = db.query(LawSection).join(Law).filter(
            Law.act_name.ilike(f"%{act_name_substr}%"),
            LawSection.section_number == str(section_num)
        ).first()

        if query:
            return {
                "verified": True,
                "act_name": query.law.act_name,
                "section": query.section_number,
                "title": query.title,
                "source_url": query.source_url,
                "status_badge": "VERIFIED_AUTHORITY"
            }
        return {
            "verified": False,
            "act_name": act_name_substr,
            "section": section_num,
            "title": "Authority Not Verified",
            "source_url": None,
            "status_badge": "UNVERIFIED_AUTHORITY_WARNING"
        }
