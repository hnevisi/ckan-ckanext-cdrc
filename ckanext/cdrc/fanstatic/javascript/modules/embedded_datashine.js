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

      var descriptionLines = momconfig.description.map(function(d){return new ol.Attribution({"html": d + '<br/>'})});
      descriptionLines.push(new ol.Attribution({"html": "<br/><br/>"}))
      $('#map-of-the-month-title').html(momconfig.title);
      $('#map-of-the-month-link').attr("href", momconfig.map_link);
      layerData = new ol.layer.Tile({
        title: "",
        source: new ol.source.XYZ({
          url: momconfig.tile_url,
          crossOrigin: 'null',
          attributions: descriptionLines
        })
      });
      buildingLayer = new ol.layer.Tile({
        title: "",
        source: new ol.source.XYZ({
          url: "https://maps.cdrc.ac.uk/tiles/shine_urbanmask_dark/{z}/{x}/{y}.png",
          crossOrigin: 'null',
        })
      });
      labelLayer = new ol.layer.Tile({
        title: "",
        source: new ol.source.XYZ({
          url: "https://maps.cdrc.ac.uk/tiles/shine_labels_cdrc/{z}/{x}/{y}.png",
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


