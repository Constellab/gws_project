import reflex as rx
from gws_project.company.company import Company
from gws_project.company.company_service import CompanyService
from gws_reflex_main import ReflexMainState


class CompanyPageState(rx.State):
    """State for managing the current company object with caching.

    Detects `company_id_param` from the URL and caches the loaded Company object,
    avoiding redundant database queries across the pages/components that need it.
    """

    _cached_company: Company | None = None

    async def company(self) -> Company | None:
        """Get the current company from URL parameters.
        The method should not be named get_company because the get_object method
        call a get_company which make the reflex compiler confused.

        :return: The loaded Company object, or None if not found
        :rtype: Optional[Company]
        """
        return await self.get_object()

    async def get_object(self) -> Company | None:
        """Get the current company from URL parameters with caching.

        :return: The loaded Company object, or None if not found
        :rtype: Optional[Company]
        """
        company_id = getattr(self, "company_id_param", None)
        if not company_id:
            return None

        if self._cached_company is not None and self._cached_company.id == company_id:
            return self._cached_company

        main_state = await self.get_state(ReflexMainState)
        with await main_state.authenticate_user():
            company_service = CompanyService()
            company = company_service.get_company(company_id)
            self._cached_company = company
            return company

    async def refresh_object(self) -> Company | None:
        """Refresh (reload) the current company from URL parameters.

        :return: The reloaded Company object, or None if not found
        :rtype: Optional[Company]
        """
        self._cached_company = None
        return await self.get_object()
