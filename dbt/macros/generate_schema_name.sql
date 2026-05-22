{#-
  Override of dbt's default generate_schema_name.

  Default behavior concatenates target.schema with the model's +schema config
  (e.g. "main" + "prep_football" = "main_prep_football"). We want the +schema
  config to win verbatim, falling back to the target's schema if no override.
-#}
{% macro generate_schema_name(custom_schema_name, node) -%}
    {%- set default_schema = target.schema -%}
    {%- if custom_schema_name is none -%}
        {{ default_schema }}
    {%- else -%}
        {{ custom_schema_name | trim }}
    {%- endif -%}
{%- endmacro %}
