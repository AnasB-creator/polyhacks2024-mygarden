#---- Define server logic for the Shiny app ----#

function(input, output, session) {

  # generate map
  output$map <- leaflet::renderLeaflet({

    leaflet::leaflet(data = cities) %>%
      leaflet::addTiles() %>%
      leaflet::addMarkers(
        lng = ~longitude,
        lat = ~latitude,
        layerId = ~city_name,
        label = ~city_name
      )
  })

  # map marker data
  mapMarker <- shiny::reactiveVal("")

  # update selected city on marker click
  shiny::observeEvent(input$map_marker_click, {

    # get selected marker data
    citySelected <- input$map_marker_click
    # get current marker data
    cityCurrent <- cities %>%
      dplyr::filter(city_name == mapMarker())

    # remove and add current marker
    if (mapMarker() != "") {
      leaflet::leafletProxy("map") %>%
        leaflet::removeMarker(mapMarker()) %>%
        leaflet::addMarkers(
          lng = cityCurrent$longitude,
          lat = cityCurrent$latitude,
          layerId = cityCurrent$city_name,
          label = cityCurrent$city_name
        )
    }

    # remove and add selected pin marker
    leaflet::leafletProxy("map") %>%
      leaflet::removeMarker(citySelected$id) %>%
      leaflet::addMarkers(
        lng = citySelected$lng,
        lat = citySelected$lat,
        layerId = citySelected$id,
        label = citySelected$id,
        icon = iconSelected
      )

    # update current marker
    mapMarker(citySelected$id)
  })

  # selected city output
  output$mapCity <- renderText({
    shiny::validate(shiny::need(mapMarker(), message = "Select a city"))

    paste0("Your selected city is: ", mapMarker())
  })

}
