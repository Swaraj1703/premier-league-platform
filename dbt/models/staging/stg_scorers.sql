{#-
  Staging view for scorers. Surrogate key + flatten nested player/team + cast date strings.
  Materialized as a view in prep_football.

  NOTE: Surrogate key is currently `player_id` alone because the scorers resource does not
  preserve competition + season context from the API envelope (see issue #23). Once that
  resource enrichment lands, the SK input widens to [player_id, competition_id, season_id].
  Today the warehouse holds exactly one (competition, season) of scorers, so player_id is
  unique by construction.
-#}

with source as (
    select * from {{ source('raw_football', 'scorers') }}
),

renamed as (
    select
        player__id                                  as player_id,
        player__name                                as player_name,
        player__first_name                          as player_first_name,
        player__last_name                           as player_last_name,
        cast(player__date_of_birth as date)         as player_date_of_birth,
        player__nationality                         as player_nationality,
        player__section                             as player_section,
        player__shirt_number                        as player_shirt_number,
        player__last_updated                        as player_last_updated,
        team__id                                    as team_id,
        team__name                                  as team_name,
        team__short_name                            as team_short_name,
        team__tla                                   as team_tla,
        team__crest                                 as team_crest,
        team__address                               as team_address,
        team__website                               as team_website,
        team__founded                               as team_founded_year,
        team__club_colors                           as team_club_colors,
        team__venue                                 as team_venue,
        team__last_updated                          as team_last_updated,
        played_matches,
        goals,
        assists,
        penalties
    from source
)

select
    {{ dbt_utils.generate_surrogate_key(['player_id']) }} as player_sk,
    *
from renamed
