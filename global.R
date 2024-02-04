
# Setup -------------------------------------------------------------------

library(conflicted)          # conflict resolution on package loading
library(magrittr)            # pipe operator & helpers
library(dplyr)               # data manipulation
library(DBI)                 # database interface
library(RPostgres)           # Postgres driver
library(shiny)               # web app framework
library(shinyWidgets)        # advanced Shiny widgets
library(bslib)               # Bootstrap-based ui tooklit
library(reticulate)          # R interface for Python
library(sf)                  # simple features access
library(leaflet)             # interactive web maps

# prefer base R packages on conflicts
conflicted::conflict_prefer_all("stats", quiet = TRUE)
conflicted::conflict_prefer_all("utils", quiet = TRUE)

# database connection
con <- DBI::dbConnect(
  RPostgres::Postgres(),
  dbname = "dev",
  host = "ep-soft-unit-a5tg3j5a.us-east-2.aws.neon.tech",
  port = 5432,
  user = "roppa070",
  password = "xqchfg1d2YIb"
)

reticulate::source_python("py/sample.py")


# Helpers -----------------------------------------------------------------

## misc ----

# get all data from table
dbGetTable <- function(tbl) {

  return(
    DBI::dbGetQuery(con, paste("SELECT * FROM", tbl)) %>%
      tibble::tibble() # as tibble
  )
}


## ui ----

# slider input returning an importance level
importanceInput <- function(inputId, label, levels) {

  return(
    shinyWidgets::sliderTextInput(
      inputId = inputId,
      label = label,
      choices = levels$name,
      selected = levels$name[3],
      grid = TRUE,
      hide_min_max = TRUE,
      force_edges = TRUE
    )
  )
}


# selected pin icon
iconSelected <- leaflet::makeIcon(
  iconUrl = "www/icons/map-pin-icon.svg",
  iconWidth = 25, iconHeight = 41,
  iconAnchorX = 12, iconAnchorY = 41
)


## server ----

# ...


# Data --------------------------------------------------------------------

## theme ----
app_theme <- bslib::bs_theme(
  "font-size-base" = "0.8rem"
)

## raw data ----

# importance levels
importance_levels <- tibble::tibble(
  name = c("Not Important", "Less Important", "Important", "Very Important"),
  value = 0:3
)

# db data
cities <- dbGetTable("cities")
plants <- dbGetTable("plants")
