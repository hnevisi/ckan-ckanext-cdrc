this.ckan.module('embedded-datashine', function ($, _) {
  $(document).ready(function(){
    var tileName = ",c11_ew_-QS201EW0002-QS201EW0001-wd-equal_bin-0.871304-0.167098-oa-equal_bin-0.817827-0.220243-cb-RdYlGn-8-0";
    layerData = new ol.layer.Tile({
      title: "",
      source: new ol.source.XYZ({
        url: "http://datashine.org.uk/tiler/" + tileName + "/{z}/{x}/{y}.png",
        crossOrigin: 'null',
        attributions: [
          ol.source.OSM.ATTRIBUTION,
          new ol.Attribution({ 'html': '<br />Census data: National Statistics, licensed under the Open Government Licence v.3.0.<br />' }),
          new ol.Attribution({ 'html': 'DataShine was created by Oliver O&apos;Brien and James Cheshire at UCL CASA/UCL Geography.<br />' })
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
