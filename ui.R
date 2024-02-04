#---- User interface for the Shiny app ----#

bslib::page_fillable(
  theme = app_theme,

  # page layout
  bslib::layout_columns(
    col_widths = c(4,8),
    # app info & inputs ----
    bslib::card(
      class = "well border-0",

      ## app info ----

      # title
      shiny::titlePanel("My Garden"),

      # instructions
      shiny::p(
        "First select your city on the map and input your garden size, then select
        your level of importance for each of the optimization parameters: total annual
        value of the harvests, the amount of calories produced, the amount of emissions
        saved and the preferred sowing-to-harvesting time."
      ),

      ## inputs ----

      # map
      shiny::textOutput(outputId = "mapCity"),
      leaflet::leafletOutput("map", height = "25vh"),

      # garden size
      shiny::numericInput(
        inputId = "gardenArea",
        label = "Enter your garden's size in square feet",
        value = 2, min = 0, step = 1,
        width = "300px"
      ),

      # optimization coefficients
      shiny::h6("How important for you is it to ..."),
      bslib::layout_columns(
        col_widths = c(6,6),
        # fill = FALSE,
        importanceInput("coeffValue", "maximize value ($)?", importance_levels),
        importanceInput("coeffCal", "maximize produced calories?", importance_levels)
      ),
      bslib::layout_columns(
        col_widths = c(6,6),
        # fill = FALSE,
        importanceInput("coeffCO2", "maximize saved CO2 emissions?", importance_levels),
        importanceInput("coeffTime", "minimize sowing-to-harvesting time?", importance_levels)
      ),

      ## run optimization ----
      shiny::div(
        shiny::actionButton(
          "runOpt",
          label = "Suggest a garden plan"
        )
      )
    ),

    # results ----
    bslib::card(
      class = NULL
    )
  )
)
