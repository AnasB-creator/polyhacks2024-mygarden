library(conflicted)          # conflict resolution on package loading
library(shiny)               # web app framework
library(shinyWidgets)        # advanced Shiny widgets
library(bslib)               # Bootstrap-based ui tooklit
library(reticulate)          # R interface for Python

# prefer base R packages on conflicts
conflicted::conflict_prefer_all("stats", quiet = TRUE)
conflicted::conflict_prefer_all("utils", quiet = TRUE)
