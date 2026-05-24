{#-
  Staging view for teams. Surrogate key + flatten nested coach/area + cast date strings.
  Materialized as a view in prep_football.
-#}

with source as (
    select * from {{ source('raw_football', 'teams') }}
),

renamed as (
    select
        id                                              as team_id,
        name                                            as team_name,
        short_name                                      as team_short_name,
        tla                                             as team_tla,
        crest,
        address,
        website,
        founded                                         as founded_year,
        club_colors,
        venue,
        last_updated,
        coach__id                                       as coach_id,
        coach__first_name                               as coach_first_name,
        coach__last_name                                as coach_last_name,
        coach__name                                     as coach_name,
        cast(coach__date_of_birth as date)              as coach_date_of_birth,
        coach__nationality                              as coach_nationality,
        strptime(coach__contract__start, '%Y-%m')::date as coach_contract_start_month,
        strptime(coach__contract__until, '%Y-%m')::date as coach_contract_end_month,
        area__id                                        as area_id,
        area__name                                      as area_name,
        area__code                                      as area_code,
        area__flag                                      as area_flag
    from source
)

select
    {{ dbt_utils.generate_surrogate_key(['team_id']) }} as team_sk,
    *
from renamed
