with bronze as (
    select * from {{ source('bronze', 'api_football_fixtures') }} -- choix de la shcema et de la table
),

versions as (
    select
        *,
        row_number() over (
            partition by fixture__id
            order by _date_depot desc, _date_chargement_bronze desc
        ) as rang_version
    from bronze
)

select
    -- Match
    fixture__id                 as id_match,
    fixture__date               as date_heure_match,
    fixture__timestamp          as date_heure_match_unix,
    fixture__timezone           as fuseau_horaire_match,
    fixture__referee            as arbitre,
    fixture__periods__first     as debut_premiere_periode_unix,
    fixture__periods__second    as debut_deuxieme_periode_unix,

    -- Statut du match
    fixture__status__short      as code_statut_match,
    fixture__status__long       as libelle_statut_match,
    fixture__status__elapsed    as minutes_jouees,
    fixture__status__extra      as minutes_supplementaires,

    -- Stade
    fixture__venue__id          as id_stade,
    fixture__venue__name        as nom_stade,
    fixture__venue__city        as ville_stade,

    -- Compétition
    league__id                  as id_competition,
    league__name                as nom_competition,
    league__country             as pays_competition,
    league__logo                as logo_competition_url,
    league__flag                as drapeau_pays_url,
    league__season              as saison,
    league__round               as journee,
    league__standings           as competition_avec_classement,

    -- Équipe à domicile
    teams__home__id             as id_equipe_domicile,
    teams__home__name           as nom_equipe_domicile,
    teams__home__logo           as logo_equipe_domicile_url,
    teams__home__winner         as equipe_domicile_gagnante,

    -- Équipe à l'extérieur
    teams__away__id             as id_equipe_exterieur,
    teams__away__name           as nom_equipe_exterieur,
    teams__away__logo           as logo_equipe_exterieur_url,
    teams__away__winner         as equipe_exterieur_gagnante,

    -- Buts
    goals__home                 as buts_domicile,
    goals__away                 as buts_exterieur,

    -- Score par phase
    score__halftime__home       as score_mi_temps_domicile,
    score__halftime__away       as score_mi_temps_exterieur,
    score__fulltime__home       as score_fin_temps_reglementaire_domicile,
    score__fulltime__away       as score_fin_temps_reglementaire_exterieur,
    score__extratime__home      as score_prolongation_domicile,
    score__extratime__away      as score_prolongation_exterieur,
    score__penalty__home        as tirs_au_but_domicile,
    score__penalty__away        as tirs_au_but_exterieur,

    -- Colonnes techniques (traçabilité)
    _dlt_load_id                as tech_id_chargement_dlt,
    _dlt_id                     as tech_id_ligne_dlt,
    _date_depot                 as tech_date_depot_landing,
    _fichier_source             as tech_fichier_source,
    _date_chargement_bronze     as tech_date_chargement_bronze

from versions
where rang_version = 1


