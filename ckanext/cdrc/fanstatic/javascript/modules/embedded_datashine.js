this.ckan.module('embedded-datashine', function ($, _) {
  $(document).ready(function(){
    // var tileName = ",c11_ew_-QS302EW0002-QS302EW0001-wd-standard_dev-0.470440000-0.052875400-oa-standard_dev-0.465285000-0.088207400-cb-RdYlBu-8-0";
    var tileName = "http://maps.cdrc.ac.uk/tiles/imd1015change_11l";
    layerData = new ol.layer.Tile({
      title: "",
      source: new ol.source.XYZ({
        // url: "http://datashine.org.uk/tiler/" + tileName + "/{z}/{x}/{y}.png",
        url: tileName + "/{z}/{x}/{y}.png",
        crossOrigin: 'null',
        attributions: [
          new ol.Attribution({ 'html': 'This map shows the change of index of multiple deprivation ranks from 2010 to 2015. <br />' }),
          new ol.Attribution({ 'html': 'Bluer areas are becoming less deprived at a faster rate than redder areas. <br />' }),
          new ol.Attribution({ 'html': 'A decrease may still indicate a less deprived area in absolute terms. The 2010 rank is based on a fitting to 2011 LSOAs performed by Public Health England. <br />' }),
          new ol.Attribution({ 'html': 'To search and download the IMD data click <a href="https://data.cdrc.ac.uk/dataset?q=index+of+deprivation+2010+2015" style="text-decoration: underline;">here</a>, or to browse more maps click <a h$
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
