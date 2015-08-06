this.ckan.module('embedded-datashine', function ($, _) {
  $(document).ready(function(){
    var tileName = ",c11_ew_-QS302EW0002-QS302EW0001-wd-standard_dev-0.470440000-0.052875400-oa-standard_dev-0.465285000-0.088207400-cb-RdYlGn-8-0";
    layerData = new ol.layer.Tile({
      title: "",
      source: new ol.source.XYZ({
        url: "http://datashine.org.uk/tiler/" + tileName + "/{z}/{x}/{y}.png",
        crossOrigin: 'null',
        attributions: [
          ol.source.OSM.ATTRIBUTION,
          new ol.Attribution({ 'html': '<br />Census data: National Statistics, licensed under the Open Government Licence v.3.0.<br />' }),
          new ol.Attribution({ 'html': 'DataShine was created by Oliver O&apos;Brien and James Cheshire at UCL CASA/UCL Geography.<br />' }),
          new ol.Attribution({ 'html': '<h3>Percentages of People in Good Health (Ward)</h3> See more on <a href="http://datashine.org.uk" style="text-decoration: underline;">DataShine</a> and <a href="http://maps.cdrc.ac.uk" style="text-decoration: underline;">CDRC Maps</a>' })
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
