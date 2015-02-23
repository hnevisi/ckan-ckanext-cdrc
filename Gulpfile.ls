gulp = require \gulp

tinylr = require \tiny-lr

port = 35729

gulp.task \livereload !->
  tinylr := (require \tiny-lr)()
  tinylr.listen port

notifyLiveReload = (e) !->
  fileName = require \path .relative(__dirname, e.path)
  tinylr.changed body: files: fileName

gulp.task \watch, [\livereload], !->
  gulp.watch '**/*.css', notifyLiveReload
  gulp.watch '**/*.html', notifyLiveReload

gulp.task \default, [\watch]
