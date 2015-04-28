gulp = require \gulp
less = require \gulp-less

tinylr = require \tiny-lr

port = 35729

gulp.task \livereload !->
  tinylr := (require \tiny-lr)()
  tinylr.listen port

notify-lr = (e) ->
  fileName = require \path .relative(__dirname, e.path)
  tinylr.changed body: files: fileName

gulp.task \less ->
  gulp.src './ckanext/cdrc/public/less/main.less'
    .pipe less!
    .pipe gulp.dest './ckanext/cdrc/fanstatic/css'
  notify-lr


gulp.task \watch, [\livereload], !->
  gulp.watch '**/*.less', [\less]
  gulp.watch '**/*.css', notify-lr
  gulp.watch '**/*.html', notify-lr


gulp.task \default, [\watch]
