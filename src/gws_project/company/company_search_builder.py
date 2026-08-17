from gws_core import SearchBuilder

from gws_project.company.company import Company
from gws_project.company.company_dto import CompanyStatus


class CompanySearchBuilder(SearchBuilder):
    def __init__(self) -> None:
        super().__init__(Company, default_orders=[Company.name])

    def add_text_search(self, search_text: str) -> "CompanySearchBuilder":
        """Filter the search query by a text search on the company name"""
        like_pattern = f"%{search_text}%"
        self.add_expression(Company.name.ilike(like_pattern))

        return self

    def add_status_filter(self, status: CompanyStatus) -> "CompanySearchBuilder":
        """Filter the search query by company status"""
        self.add_expression(Company.status == status)
        return self
