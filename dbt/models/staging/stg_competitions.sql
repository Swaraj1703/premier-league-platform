{#-
  Staging view for competitions. Surrogate key + minimal renames + snake_case enforcement.
  Materialized as a view in prep_football (config in dbt_project.yml).
-#}

with source as (
    select * from {{ source('raw_football', 'competitions') }}
),

renamed as (
    select
        id                                          as competition_id,
        code                                        as competition_code,
        name                                        as competition_name,
        type                                        as competition_type,
        emblem,
        last_updated,
        current_season__id                          as current_season_id,
        cast(current_season__start_date as date)    as current_season_start_date,
        cast(current_season__end_date as date)      as current_season_end_date,
        current_season__current_matchday            as current_season_current_matchday,
        area__id                                    as area_id,
        area__name                                  as area_name,
        area__code                                  as area_code
    from source
)

select
    {{ dbt_utils.generate_surrogate_key(['competition_id']) }} as competition_sk,
    *
from renamed
