class CompanyAppRouter:
    @staticmethod
    def get_company_list_url() -> str:
        """Get the URL for the company list page.

        :return: The company list URL
        :rtype: str
        """
        return "/companies"

    @staticmethod
    def get_company_detail_url(company_id: str) -> str:
        """Get the URL for the company detail page.

        :param company_id: The ID of the company
        :type company_id: str
        :return: The company detail URL
        :rtype: str
        """
        return f"/company/{company_id}"
