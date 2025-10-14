from gws_core import (ConfigParams, AppConfig, AppType, OutputSpec,
                      OutputSpecs, ReflexResource, Task, TaskInputs,
                      TaskOutputs, app_decorator, task_decorator, 
                      InputSpecs, ConfigSpecs)


@app_decorator("ProjectAppAppConfig", app_type=AppType.REFLEX,
               human_name="Generate ProjectApp app")
class ProjectAppAppConfig(AppConfig):

    # retrieve the path of the app folder, relative to this file
    # the app code folder starts with a underscore to avoid being loaded when the brick is loaded
    def get_app_folder_path(self):
        return self.get_app_folder_from_relative_path(__file__, "_project_app")


@task_decorator("GenerateProjectApp", human_name="Generate ProjectApp app",
                style=ReflexResource.copy_style())
class GenerateProjectApp(Task):
    """
    Task that generates the ProjectApp app.
    """

    input_specs = InputSpecs()
    output_specs = OutputSpecs({
        'reflex_app': OutputSpec(ReflexResource)
    })

    config_specs = ConfigSpecs({})

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        """ Run the task """

        reflex_app = ReflexResource()

        reflex_app.set_app_config(ProjectAppAppConfig())
        reflex_app.name = "ProjectApp"

        return {"reflex_app": reflex_app}
