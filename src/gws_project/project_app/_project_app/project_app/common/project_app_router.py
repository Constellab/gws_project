

class ProjectAppRouter:

    @staticmethod
    def get_project_list_url() -> str:
        """Get the URL for the project list page.

        :return: The project list URL
        :rtype: str
        """
        return "/"

    @staticmethod
    def get_project_detail_url(project_id: str) -> str:
        """Get the URL for the project detail page.

        :param project_id: The ID of the project
        :type project_id: str
        :return: The project detail URL
        :rtype: str
        """
        return f"/project/{project_id}"

    @staticmethod
    def get_task_detail_url(task_id: str) -> str:
        """Get the URL for the task detail page.

        :param task_id: The ID of the task
        :type task_id: str
        :return: The task detail URL
        :rtype: str
        """
        return f"/task/{task_id}"

    @staticmethod
    def get_kanban_url() -> str:
        """Get the URL for the kanban board page.

        :return: The kanban board URL
        :rtype: str
        """
        return "/kanban"

    @staticmethod
    def get_project_template_list_url() -> str:
        """Get the URL for the project template list page.

        :return: The project template list URL
        :rtype: str
        """
        return "/templates"

    @staticmethod
    def get_project_template_detail_url(template_id: str) -> str:
        """Get the URL for the project template detail page.

        :param template_id: The ID of the project template
        :type template_id: str
        :return: The project template detail URL
        :rtype: str
        """
        return f"/template/project/{template_id}"

    @staticmethod
    def get_task_template_detail_url(task_template_id: str) -> str:
        """Get the URL for the task template detail page.

        :param task_template_id: The ID of the task template
        :type task_template_id: str
        :return: The task template detail URL
        :rtype: str
        """
        return f"/template/task/{task_template_id}"
