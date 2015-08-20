this.ckan.module('embedded-datashine', function ($, _) {
  $(document).ready(function(){
    var tileName = ",c11_ew_-QS302EW0002-QS302EW0001-wd-standard_dev-0.470440000-0.052875400-oa-standard_dev-0.465285000-0.088207400-cb-RdYlGn-8-0";
    layerData = new ol.layer.Tile({
      title: "",
      source: new ol.source.XYZ({
        url: "http://datashine.org.uk/tiler/" + tileName + "/{z}/{x}/{y}.png",
        crossOrigin: 'null',
        attributions: [
          new ol.Attribution({ 'html': '<br />Census data: National Statistics, licensed under the Open Government Licence v.3.0.<br />' }),
          new ol.Attribution({ 'html': 'DataShine was created by Oliver O&apos;Brien and James Cheshire at UCL CASA/UCL Geography.<br />' }),
          new ol.Attribution({ 'html': 'This map shows the % of people who are deemed as in "good health" as recorded by the 2011 census. <br />' }),
          new ol.Attribution({ 'html': 'The CDRC are interested in how these patterns vary geographically, and how these outcomes relate to consumption.  <br />' }),
          new ol.Attribution({ 'html': 'To search and download census data click <a href="https://data.cdrc.ac.uk/dataset?q=census+data" style="text-decoration: underline;">here</a>, or to browse more maps click <a href="http://maps.cdrc.ac.uk" style="text-decoration: underline;">here</a>' }),
          new ol.Attribution({ 'html': '<br /><br /><br /><br />' }),
        ]
      })
    });

    olMap = new ol.Map({
      target: "map-container",
      interactions: ol.interaction.defaults({mouseWheelZoom:false}),
      layers:
      [
        layerData
      ],
      controls: ol.control.defaults({}),
      view: new ol.View({
        projection: "EPSG:3857",
        maxZoom: 14,
        minZoom: 8,
        zoom: 8,
        center: ol.proj.transform([0, 51.51], "EPSG:4326", "EPSG:3857"),
        restrictedExtent: ol.proj.transformExtent([-10, 48.5, 4, 62], "EPSG:4326", "EPSG:3857") /* Aggressive to minimise the jumping scrolling quirk in OL3. */
      })
    });

  });
});
