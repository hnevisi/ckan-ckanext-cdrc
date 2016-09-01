this.ckan.module('embedded-datashine', function ($, _) {
  $(document).ready(function(){
    $.getJSON('/api/3/action/momconfig_show', function(rtn){
      var momconfig = rtn.result;
    // var momconfig = {
    //   title: "aaa",
    //   map_link: "http://maps.cdrc.ac.uk",
    //   tile_url: "http://maps.cdrc.ac.uk/tiles/popchg_11_14_gblsoa/{z}/{x}/{y}.png",
    //   description: ["aaa", "bbb"]
    // }

      // var tileName = ",c11_ew_-QS302EW0002-QS302EW0001-wd-standard_dev-0.470440000-0.052875400-oa-standard_dev-0.465285000-0.088207400-cb-RdYlBu-8-0";
      var tileName = "http://maps.cdrc.ac.uk/tiles/popchg_11_14_gblsoa";
      var descriptionLines = momconfig.description.map(function(d){return new ol.Attribution({"html": d + '<br/>'})});
      descriptionLines.push(new ol.Attribution({"html": "<br/><br/>"}))
      $('#map-of-the-month-title').html(momconfig.title);
      $('#map-of-the-month-link').attr("href", momconfig.map_link);
      layerData = new ol.layer.Tile({
        title: "",
        source: new ol.source.XYZ({
          // url: "http://datashine.org.uk/tiler/" + tileName + "/{z}/{x}/{y}.png",
          url: momconfig.tile_url,
          crossOrigin: 'null',
          attributions: descriptionLines
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
});


