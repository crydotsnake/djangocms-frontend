from django.apps import apps
from django.conf import settings
from django.db import connection, models

from .base import SubcommandsCommand

plugin_names = {}


plugin_migrations = {}
data_migration = {}

# Bootstrap 4
if "djangocms_bootstrap4" in apps.all_models:
    from djangocms_frontend.management import bootstrap4_migration

    plugin_migrations.update(bootstrap4_migration.plugin_migrations)
    data_migration.update(bootstrap4_migration.data_migration)
# Styled link
if "djangocms_styledlink" in apps.all_models:
    from djangocms_frontend.management import styled_link_migration

    plugin_migrations.update(styled_link_migration.plugin_migrations)
    data_migration.update(styled_link_migration.data_migration)


def migrate_to_djangocms_frontend(apps, schema_editor):
    cnt = 0
    for plugin_model, fields in plugin_migrations.items():
        old, new = plugin_model.split(" -> ")
        old_app, old_model = old.rsplit(".", 1)
        new_app, new_model = new.rsplit(".", 1)
        if old_app in apps.all_models:
            OldPluginModel = apps.get_model(old_app, old_model)
            NewPluginModel = apps.get_model(new_app, new_model)
            for obj in OldPluginModel.objects.all():
                #
                new_obj = NewPluginModel()
                new_obj_fields = [field.name for field in new_obj._meta.get_fields()]
                new_obj.id = obj.id
                new_obj.placeholder = obj.placeholder
                new_obj.parent = obj.parent
                new_obj.position = obj.position
                new_obj.language = obj.language
                new_obj.creation_date = obj.creation_date
                if hasattr(obj, "depth"):  # cms v3
                    new_obj.depth = obj.depth
                    new_obj.numchild = obj.numchild
                    new_obj.path = obj.path
                new_obj.plugin_type = (
                    plugin_names[new_model]
                    if new_model in plugin_names
                    else new_model + "Plugin"
                )
                # Add something like `new_obj.field_name = obj.field_name` for any field in the the new plugin
                for field in fields:
                    if field in data_migration:
                        data_migration[field](obj, new_obj)
                    else:
                        if " -> " in field:
                            old_field, new_field = field.split(" -> ")
                        else:
                            old_field, new_field = field, field
                        value = (
                            old_field[1:-1]
                            if old_field[0] == "("
                            else getattr(obj, old_field)
                        )
                        if value == "":
                            value = None
                        if new_field in new_obj_fields:
                            setattr(new_obj, new_field, value)
                        else:
                            if isinstance(value, models.Model):  # related field
                                value = {
                                    "model": "{}.{}".format(
                                        value._meta.app_label,
                                        value._meta.model_name,
                                    ),
                                    "pk": value.pk,
                                }
                            elif isinstance(
                                value, models.QuerySet
                            ):  # related many field
                                value = {
                                    "model": "{}.{}".format(
                                        value.model._meta.app_label,
                                        value.model._meta.model_name,
                                    ),
                                    "p_keys": list(value.values_list("pk", flat=True)),
                                }
                            new_obj.config[new_field] = value
                new_obj.save()
                # Now delete old plugin from its table w/o checking for child plugins
                with connection.cursor() as cursor:
                    cursor.execute(
                        f"DELETE FROM `{obj._meta.db_table}` WHERE cmsplugin_ptr_id={obj.id};"
                    )
                cnt += 1
                print(f"{cnt:7}", end="\r")
                # Copy any many to many field after save:`new_plugin.many2many.set(old_plugin.many2many.all())`
        else:
            print(f"{old_app} not installed.")
    print()


blog_example = """
You have djangocms_blog installed. Consider adding the following
lines to your settings.py:

    DJANGOCMS_FRONTEND_LINK_MODELS = [
        {
            "type": _("Blog pages"),
            "class_path": "djangocms_blog.models.Post",
            "filter": {"publish": True, "app_config_id": 1},
            "search": "translations__title",
        },
    ]

This will allow editors to directly link to blog posts. Also,
blog posts can easily link amongst themselves.

See for https://djangocms-frontend.readthedocs.io/en/latest/howto_guides.html
for more information.
"""

doc_reference = """
You may want to consider allowing editors to directly link to
a page generated by these models.

See for https://djangocms-frontend.readthedocs.io/en/latest/howto_guides.html
for more information.
"""


class Migrate(SubcommandsCommand):
    help = "Migrates plugins djangocms_bootstrap4 to djangocms_frontend"
    command_name = "migrate"

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Migrating plugins"))
        migrate_to_djangocms_frontend(apps, None)
        self.stdout.write(self.style.SUCCESS("Successfully migrated plugins"))
        self.stdout.write()
        if getattr(settings, "DJANGOCMS_FRONTEND_LINK_MODELS", None) is None:
            self.check_for_link_targets()

    def check_for_link_targets(self):
        self.stdout.write(
            self.style.SUCCESS(
                "Checking installed apps for potential link destinations"
            )
        )
        blog = False
        count = 0
        for app, app_models in apps.all_models.items():
            if app != "cms":
                for _, model in app_models.items():
                    if hasattr(model, "get_absolute_url"):
                        count += 1
                        self.stdout.write(
                            self.style.NOTICE(
                                f"App {app}'s {model.__name__} model is a suitable link destination."
                            )
                        )
            if app == "djangocms_blog":
                blog = True
        if count:
            self.stdout.write(
                self.style.SUCCESS(f"{count} potential link destinations found.")
            )
            if blog:
                self.stdout.write(self.style.WARNING(blog_example))
            else:
                self.stdout.write(self.style.WARNING(doc_reference))

        else:
            self.stdout.write(
                self.style.SUCCESS(
                    "No further link destinations found. Setup complete."
                )
            )
