/* Media Grid
 * Super simple plugin that waits for all the images to be loaded in the media
 * grid and then applies the jQuery.masonry to then
 */
this.ckan.module('media-grid', function ($, _) {
  $('#group-list').mixItUp({selectors:{target: '.media-item'}, animation:{enable: false}})
});
