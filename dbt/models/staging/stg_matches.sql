{#-
  Staging view for matches. Surrogate key + flatten nested score/team/season/competition/area
  + cast season date strings + reorder triple-nested score columns.
  Materialized as a view in prep_football.
-#}

with source as (
    select * from {{ source('raw_football', 'matches') }}
),

renamed as (
    select
        id                                  as match_id,
        utc_date                            as match_utc_datetime,
        status                              as match_status,
        matchday,
        stage,
        last_updated,
        odds__msg                           as odds_msg,
        score__winner                       as score_winner,
        score__duration                     as score_duration,
        -- Triple-nested score cols renamed: `score__half_time__home` -> `half_time_home_score`.
        score__half_time__home              as half_time_home_score,
        score__half_time__away              as half_time_away_score,
        score__full_time__home              as full_time_home_score,
        score__full_time__away              as full_time_away_score,
        home_team__id                       as home_team_id,
        home_team__name                     as home_team_name,
        home_team__short_name               as home_team_short_name,
        home_team__tla                      as home_team_tla,
        home_team__crest                    as home_team_crest,
        away_team__id                       as away_team_id,
        away_team__name                     as away_team_name,
        away_team__short_name               as away_team_short_name,
        away_team__tla                      as away_team_tla,
        away_team__crest                    as away_team_crest,
        season__id                          as season_id,
        cast(season__start_date as date)    as season_start_date,
        cast(season__end_date as date)      as season_end_date,
        season__current_matchday            as season_current_matchday,
        competition__id                     as competition_id,
        competition__name                   as competition_name,
        competition__code                   as competition_code,
        competition__type                   as competition_type,
        competition__emblem                 as competition_emblem,
        area__id                            as area_id,
        area__name                          as area_name,
        area__code                          as area_code,
        area__flag                          as area_flag
    from source
)

select
    {{ dbt_utils.generate_surrogate_key(['match_id']) }} as match_sk,
    *
from renamed
