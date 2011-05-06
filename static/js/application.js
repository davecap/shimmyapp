/*
 * jQuery File Upload Plugin JS Example 4.6
 * https://github.com/blueimp/jQuery-File-Upload
 *
 * Copyright 2010, Sebastian Tschan
 * https://blueimp.net
 *
 * Licensed under the MIT license:
 * http://creativecommons.org/licenses/MIT/
 */

/*jslint unparam: true */
/*global $ */

$(function () {
    // Initialize jQuery File Upload (Extended User Interface Version):
    $('#file_upload').fileUploadUI({
        uploadTable: $('#files'),
        buildUploadRow: function (files, index, handler) {
            return $('<tr><td>' + files[index].name + '<\/td>' +
                    '<td class="file_upload_progress"><div><\/div><\/td>' +
                    '<td class="file_upload_cancel">' +
                    '<button class="ui-state-default ui-corner-all" title="Cancel">' +
                    '<span class="ui-icon ui-icon-cancel">Cancel<\/span>' +
                    '<\/button><\/td><\/tr>');
        },
        buildDownloadRow: function (file, handler) {
            return $('<tr><td>' + file.name + '<\/td><\/tr>');
        },
        beforeSend: function (event, files, index, xhr, handler, callBack) {
            $.get('/preupload', function (data) {
                handler.url = data;
                callBack();
            });
        }
    });
    
    // // Load existing files:
    // $.getJSON($('#file_upload').fileUploadUIX('option', 'url'), function (files) {
    //     var options = $('#file_upload').fileUploadUIX('option');
    //     options.adjustMaxNumberOfFiles(-files.length);
    //     $.each(files, function (index, file) {
    //         options.buildDownloadRow(file, options)
    //             .appendTo(options.downloadTable).fadeIn();
    //     });
    // });
    
});