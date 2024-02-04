#---- User interface for the Shiny app ----#

bslib::page_sidebar(
  title = "My Garden",
  theme = app_theme,
  sidebar = bslib::sidebar(
    width = "30%",
    shiny::h4("Main Options"),
    shiny::numericInput(
      inputId = "gardenArea",
      label = shiny::HTML("Enter your garden's size in m<sup>2</sup>"),
      value = 2, min = 0, step = 1
    ),
    leaflet::leafletOutput("map", height = "25vh"),
    shiny::textOutput(outputId = "mapCity"),
    shiny::h4("More Options"),
    shiny::selectInput(
      "uniquePlantsMax",
      label = "How many different plants at max?",
      choices = c("2"=2, "3"=3, "4"=4, "5"=5, "6+"=Inf),
      selected = 4
    ),
    shiny::selectInput(
      "maintLevelMax",
      label = "Max maintenance level?",
      choices = c("Low" = 1, "Medium" = 2, "High" = 3),
      selected = 2
    ),
    importanceInput("coeffValue", "Value ($):", importance_levels),
    importanceInput("coeffCal", "Calories:", importance_levels),
    importanceInput("coeffCO2", "Saved CO2 emissions:", importance_levels)
  )
)
