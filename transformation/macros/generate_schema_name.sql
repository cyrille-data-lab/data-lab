{#-
  Choix du schéma où dbt crée les tables.
  - prod (target.name = 'prod') : schéma demandé tel quel → silver, gold
  - dev et CI : préfixé par le schéma personnel → dbt_cgbale_silver
  Ainsi, le développement n'écrase jamais les schémas partagés.
-#}
{% macro generate_schema_name(custom_schema_name, node) -%}
    {%- set default_schema = target.schema -%}
    {%- if custom_schema_name is none -%}
        {{ default_schema }}
    {%- elif target.name == 'prod' or var('environnement', 'dev') == 'prod' -%}
        {{ custom_schema_name | trim }}
    {%- else -%}
        {{ default_schema }}_{{ custom_schema_name | trim }}
    {%- endif -%}
{%- endmacro %}