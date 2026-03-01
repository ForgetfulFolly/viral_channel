from typing import Optional, Dict
import jinja2
import logging

# Configure logging with correlation IDs
logger = logging.getLogger(__name__)

class PromptManager:
    def __init__(self, template_dir: str = "config/prompts/") -> None:
        """Initialize with template directory path."""
        self.env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(template_dir),
            autoescape=False
        )

    def load_prompt(self, template_name: str, **variables) -> str:
        """Load and render a Jinja2 template with variables.

        Args:
            template_name (str): The name of the template file.
            **variables: Variables to pass to the template for rendering.

        Returns:
            str: Rendered template as a string.

        Raises:
            jinja2.TemplateNotFound: If the template file is not found.
            jinja2.TemplateError: If there is an error during template rendering.
        """
        try:
            template = self.env.get_template(template_name)
            rendered_prompt = template.render(**variables)
            return rendered_prompt
        except jinja2.TemplateNotFound as e:
            logger.error(f"Template '{template_name}' not found: {e}")
            raise
        except jinja2.TemplateError as e:
            logger.error(f"Error rendering template '{template_name}': {e}")
            raise