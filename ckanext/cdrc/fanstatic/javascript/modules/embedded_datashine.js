this.ckan.module('embedded-datashine', function ($, _) {
  $(document).ready(function(){
    // var tileName = ",c11_ew_-QS302EW0002-QS302EW0001-wd-standard_dev-0.470440000-0.052875400-oa-standard_dev-0.465285000-0.088207400-cb-RdYlBu-8-0";
    var tileName = "http://maps.cdrc.ac.uk/tiles/popchg_11_14_gblsoa";
    $('#map-of-the-month-title').html("Small-Area Population Change 2011-2014");
    $('#map-of-the-month-link').attr("href", "http://maps.cdrc.ac.uk/#/metrics/popchange/default/BTTTFTT/10/-0.1499/51.5200/");
    layerData = new ol.layer.Tile({
      title: "",
      source: new ol.source.XYZ({
        // url: "http://datashine.org.uk/tiler/" + tileName + "/{z}/{x}/{y}.png",
        url: tileName + "/{z}/{x}/{y}.png",
        crossOrigin: 'null',
        attributions: [
          new ol.Attribution({ 'html': 'This map shows the population change in small-area mid-year population estimates by the ONS and NRS, between 2011 and 2014, for the approximately 40,000 LSOAs/DZs across Great Britain (England, Sc$
          new ol.Attribution({ 'html': 'To search and download the data in the map click <a href="https://data.cdrc.ac.uk/dataset/small-area-population-change-2011-14" style="text-decoration: underline;">here</a>, or to browse more maps$
          new ol.Attribution({ 'html': 'Contains data from gov.uk. Crown copyright and database right 2015. <br />' }),
          new ol.Attribution({ 'html': 'The CDRC are interested in how these patterns vary geographically, and how these outcomes relate to consumption.  <br />' }),
          new ol.Attribution({ 'html': '<br /><br /><br />' }),
        ]
      })
    });
    buildingLayer = new ol.layer.Tile({
      title: "",
      source: new ol.source.XYZ({
        url: "http://datashine.org.uk/tiles/" + "shine_urbanmask_dark" + "/{z}/{x}/{y}.png",
        crossOrigin: 'null',
      })
    });
    labelLayer = new ol.layer.Tile({
      title: "",
      source: new ol.source.XYZ({
        url: "http://datashine.org.uk/tiles/" + "shine_labels_cdrc" + "/{z}/{x}/{y}.png",
        crossOrigin: 'null',
      })
    });

    olMap = new ol.Map({
      target: "map-container",
      interactions: ol.interaction.defaults({mouseWheelZoom:false}),
      layers:
      [
        layerData,
        buildingLayer,
        labelLayer
      ],
      controls: ol.control.defaults({}),
      view: new ol.View({
        projection: "EPSG:3857",
        maxZoom: 14,
        minZoom: 8,
        zoom: 10,
        center: ol.proj.transform([0.27, 51.51], "EPSG:4326", "EPSG:3857"),
        restrictedExtent: ol.proj.transformExtent([-10, 48.5, 4, 62], "EPSG:4326", "EPSG:3857") /* Aggressive to minimise the jumping scrolling quirk in OL3. */
      })
    });

  });
});


