{#-
  Staging view for competitions. Minimal renames + snake_case enforcement.
  Materialized as a view in prep_football (config in dbt_project.yml).
-#}

select
    id            as competition_id,
    code          as competition_code,
    name          as competition_name,
    type          as competition_type,
    emblem,
    last_updated,
    area__id      as area_id,
    area__name    as area_name,
    area__code    as area_code
from {{ source('raw_football', 'competitions') }}
