$(function() {

    // console.log(document.cookie.split('; '));

//-----------------------Djangoのためのお決まり文句------------------------------//
    function getCookie(name) {
        var cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            var cookies = document.cookie.split(';');
            for (var i = 0; i < cookies.length; i++) {
                var cookie = jQuery.trim(cookies[i]);
                // Does this cookie string begin with the name we want?
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    var csrftoken = getCookie('csrftoken');

    function csrfSafeMethod(method) {
        return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
    }

    $.ajaxSetup({
        beforeSend: function (xhr, settings) {
            if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
                xhr.setRequestHeader('X-CSRFToken', csrftoken);
            }
        }
    });

    function commonPostAjax(url, data, success, error) {
        $.ajax({
            url: url,
            type: 'POST',
            data: data,
            timeout: 10000,
            dataType: 'json'
        }).done(function(data) {
            if (data.status == 'false') {
                console.log("data.status == false");
                console.log(data)
            } else {
                console.log('success');
                success(data);
            }
        }).fail(function(xhr, status, errorThrown) {
            if (error != null) {
                error(xhr, status, errorThrown);
            } else {
                console.log('statusCode : ' + xhr.status);
                console.log('message : ' + xhr.responseJSON['message']);
                console.log('status : ' + xhr.responseJSON['status']);
            }
        });
    }
//----------------------------------------------------------------------------//


    // デバック用
    // $("#post_form").submit(function(e) {
    //     e.preventDefault();
    //     var form = $(this);
    //     // console.log(form);
    //     var category = $("#id_category").find("input");
    //     // console.log(category);
    //     category.each(function(i, element) {
    //         console.log(element);
    //     });
    // });


    // タグ追加フォーム
    $("#add_tag_form").submit(function(e) {
        e.preventDefault();
        var val = $("input#add_tag").val();
        console.log("val = " + val);
        var url = 'add_tag/';
        var data = {
            'tag': val
        }
        console.log(data);
        commonPostAjax(url, data, addTagSuccess, addTagFailure);
    });

    // タグ追加成功時
    var addTagSuccess = function(data) {
        console.log("addTagSuccess");
        var param = data.param;
        var tag_name = data.tag_name;
        var tag_number = $('#id_tags > li').length;

        var html = '<li><label for="id_tags_' + tag_number
                   + '"><input type="checkbox" name="tags" value="'
                   + tag_name  + '" id="id_tags_' + tag_number
                   + '" form="post_form" checked="">' + param + '</label></li>';

        console.log(data.message);
        $('p.add_tag_success_msg').text(data.message);
        $('p.add_tag_error_msg').text('');
        $('#id_tags').append(html);
        $('#add_tag').val('');
    }

    // タグ追加失敗
    var addTagFailure = function(xhr, status, errorThrown) {
        console.log('addTagFailure');
        console.log('statusCode : ' + xhr.status);
        console.log('message : ' + xhr.responseJSON['message']);
        console.log('status : ' + xhr.responseJSON['status']);
        $('p.add_tag_success_msg').text('');
        $('p.add_tag_error_msg').text(xhr.responseJSON['message']);
    }


    // カテゴリ追加フォーム
    $("#add_category_form").submit(function(e) {
        e.preventDefault();
        var val = $("input#add_category").val();
        var url = 'add_category/';
        var data = {
            'category': val
        }
        console.log(data);
        commonPostAjax(url, data, addCategorySuccess, addCategoryFailure);
    });

    // カテゴリ追加成功時
    var addCategorySuccess = function(data) {
        var param = data.param;
        var category_name = data.category_name;
        var category_number = $('#id_category > li').length;

        var html = '<li><label for="id_category_' + category_number
                    + '"><input type="radio" name="category" value="'
                    + category_name  + '" id="id_category_' + category_number
                    + '" form="post_form" required="" checked="">' + param + '</label></li>';

        console.log(data.message);
        $('#id_category').append(html);
        $('#add_category').val('');
        $('p.add_category_success_msg').text(data.message);
        $('p.add_category_error_msg').text('');
    }

    // カテゴリ追加失敗
    var addCategoryFailure = function(xhr, status, errorThrown) {
        console.log('statusCode : ' + xhr.status);
        console.log('message : ' + xhr.responseJSON['message']);
        console.log('status : ' + xhr.responseJSON['status']);
        $('p.add_category_success_msg').text('');
        $('p.add_category_error_msg').text(xhr.responseJSON['message']);
    }



    // アカウント情報一括変更ボタン
    $("#update_all_btn").click(function(e) {
        console.log('update_all_btn');
        e.preventDefault();

        var username = $("#id_username").val();
        var email = $("#id_email").val();
        var password = $("#id_password").val();
        var new_password = $("#id_new_password").val();
        var new_password_confirm = $("#id_new_password_confirm").val();
        var data = {
            'username': username,
            'email': email,
            'password': password,
            'new_password': new_password,
            'new_password_confirm': new_password_confirm
        }

        $('#update_confirm').modal('show');
        $('#update_acount_all_btn').click(function(){
            e.preventDefault();
            $('#update_confirm').modal('hide');
            var url = 'update_account_all/';
            commonPostAjax(url, data, updateAllSuccess, updateAllFailure);
        });
    });

    // アカウント情報一括変更ボタン
    var updateAllSuccess = function(data){
        clearErrorMsg();
        location.href = location.protocol + '//' + location.host + '/login/';
        console.log('一括更新が成功しました。ログインページにリダイレクトします。');
        console.log(data);
        // var param = data.username;
        // $('#username').text(param);
    }

    var updateAllFailure = function(xhr, status, errorThrown) {
        clearErrorMsg();
        var response = xhr.responseJSON;
        var keys = Object.keys(response);
        var errorList = [];
        keys.forEach(function(value) {
            if (value.match(/.*error_msg.*/)) {
                errorList.push(value);
            }
        });

        if (errorList.length != 0) {

            console.log(errorList);
            errorList.forEach(function(value) {
                target = "p.update_" + value;
                $(target).text(xhr.responseJSON[value]);
            });
        } else {
            console.log(errorList);
            $('p.update_email_error_msg').text(xhr.responseJSON['message']);
        }

        $('p.update_account_success_msg').text('');
    }


    // ユーザーネーム変更ボタン
    $("#update_username_btn").click(function(e) {
        console.log('update_username_btn');
        e.preventDefault();
        var username = $("#id_username").val();
        var data = {
            'username': username
        }
        var url = 'update_username/';
        commonPostAjax(url, data, updateUsernameSuccess, updateUsernameFailure);
    });

    var updateUsernameSuccess = function(data) {
        console.log(data);
        clearErrorMsg();
        var param = data.username
        $(".account_detail_username").text(param);
        $(".login_username").text(param);
        $('p.update_account_success_msg').text(data.message);
    }

    var updateUsernameFailure = function(xhr, status, errorThrown) {
        clearErrorMsg();
        if (xhr.responseJSON['username_error_msg']) {
            $('p.update_username_error_msg').text(xhr.responseJSON['username_error_msg']);
        } else {
            $('p.update_username_error_msg').text(xhr.responseJSON['message']);
        }
        $('p.update_account_success_msg').text('');
    }



    // Email変更ボタン
    $("#update_email_btn").click(function(e) {
        console.log('update_email_btn');
        e.preventDefault();
        var email = $("#id_email").val();
        var data = {
            'email': email,
        }
        var url = 'update_email/';
        commonPostAjax(url, data, updateEmailSuccess, updateEmailFailure);
    });

    // Email変更成功時
    var updateEmailSuccess = function(data){
        clearErrorMsg();
        console.log(data);
        var param = data.email;
        $('.account_detail_email').text(param);
        $('p.update_account_success_msg').text(data.message);
    }

    var updateEmailFailure = function(xhr, status, errorThrown) {
        clearErrorMsg();
        if (xhr.responseJSON['email_error_msg']) {
            $('p.update_email_error_msg').text(xhr.responseJSON['email_error_msg']);
        } else {
            $('p.update_email_error_msg').text(xhr.responseJSON['message']);
        }
        $('p.update_account_success_msg').text('');
    }

    // パスワード変更ボタン → 現状未使用
    $("#update_password_btn").click(function(e) {
        console.log('update_password_btn');
        e.preventDefault();
        var password = $("#id_password").val();
        var new_password = $("#id_new_password").val();
        var new_password_confirm = $("#id_new_password_confirm").val();
        var data = {
            'password': password,
            'new_password': new_password,
            'new_password_confirm': new_password_confirm
        }
        var url = 'update_password/';
        commonPostAjax(url, data, updatePasswordSuccess, updatePasswordFailure);

        // var result = password.match(/^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[a-zA-Z\d]{8,50}$/);
        // var result = password.match(/^[a-zA-Z0-9]{8,50}$/);
        // if (result != null) {
        //     $('#update_password_error').text('');
        //     var data = {
        //         'password': password,
        //     }
        //     var url = 'update_password/';
        //     commonPostAjax(url, data, updatePasswordSuccess);
        // } else {
        //     $('#update_password_error').text(PW_VALIDATE_ERROR_MSG);
        // }
    });

    var updatePasswordSuccess = function(data){
        clearErrorMsg();
        $('p.update_account_success_msg').text(data.message + 'ログインページにリダイレクトします。');
        console.log('パスワード更新が成功しました。ログインページにリダイレクトします。');
        console.log(data);
        location.href = location.protocol + '//' + location.host + '/login/';
    }

    var updatePasswordFailure = function(xhr, status, errorThrown) {
        clearErrorMsg();
        var response = xhr.responseJSON;
        var keys = Object.keys(response);
        var errorList = [];
        keys.forEach(function(value) {
            if (value.match(/.*error_msg.*/)) {
                errorList.push(value);
            }
        });

        if (errorList.length != 0) {
            errorList.forEach(function(value) {
                target = "p.update_" + value;
                $(target).text(xhr.responseJSON[value]);
            });
        } else {
            console.log(errorList);
            $('p.update_email_error_msg').text(xhr.responseJSON['message']);
        }

        $('p.update_account_success_msg').text('');
    }

    // 記事削除フォーム
    $(".delete_confirm_btn").click(function(e) {

        form = $(this);
        console.log(form);
        var content_pk = form.val();

        // 削除確認画面表示
        $('#delete_confirm').modal('show');

        $('#delete_btn').click(function(){
            e.preventDefault();

            $('#delete_confirm').modal('hide');

            var url = 'delete_content/';
            var data = {
                'content_pk': content_pk
            }
            commonPostAjax(url, data, deleteContentSuccess);
        });
    });

    // 記事削除成功時
    var deleteContentSuccess = function(data) {
        var content_pk = data.content_pk;
        $('[content_pk="' + content_pk + '"]').remove();
    }

    function clearErrorMsg() {
        $('p.update_username_error_msg').text('');
        $('p.update_email_error_msg').text('');
        $('p.update_password_error_msg').text('');
        $('p.update_new_password_error_msg').text('');
        $('p.update_new_password_confirm_error_msg').text('');
        $('p.update_blog_title_error_msg').text('');
        $('p.update_blog_url_error_msg').text('');
    }

    // コメント承認・非承認処理
    $('.select_comment_status').change(function(e){
        var obj = $(this);
        var btn = obj.next();
        btn.prop('disabled', false);
    })

    $('.comment_ok_btn').click(function(e){
        e.preventDefault();

        form = $(this);
        var comment_pk = form.val();
        var select_value = form.siblings('.select_comment_status').val();

        var url = 'update_comments_list/';
        var data = {
            'comment_pk': comment_pk,
            'select_value': select_value
        }
        commonPostAjax(url, data, updateCommentSuccess);
    })

    var updateCommentSuccess = function(data){
        var comment_pk = data.comment_pk;
        var select_value = data.select_value;
        var comment_content = $('[comment_pk="' + comment_pk + '"]');

        if (select_value == '承認' || select_value == '非承認') {
            comment_content.find('.comment_ok_btn').prop('disabled', true);
        } else {
            comment_content.remove();
        }
    }



    $("#update_blog_title_btn").click(function(e) {
        console.log('update_blog_title_btn');
        e.preventDefault();
        var title = $("#id_title").val();
        var data = {
            'title': title
        }
        var url = 'update_blog_title/';
        commonPostAjax(url, data, updateBlogTitleSuccess, updateBlogTitleFailure);
    });

    var updateBlogTitleSuccess = function(data) {
        console.log(data);
        clearErrorMsg();
        var param = data.title
        $("#id_title").text(param);
        $('p.update_blog_success_msg').text(data.message);
    }

    var updateBlogTitleFailure = function(xhr, status, errorThrown) {
        clearErrorMsg();
        if (xhr.responseJSON['title_error_msg']) {
            $('p.update_blog_title_error_msg').text(xhr.responseJSON['title_error_msg']);
        } else {
            $('p.update_blog_title_error_msg').text(xhr.responseJSON['message']);
        }
        $('p.update_blog_success_msg').text('');
    }


    $("#update_blog_url_btn").click(function(e) {
        console.log('update_blog_url_btn');
        e.preventDefault();
        var url = $("#id_url").val();
        var data = {
            'url': url
        }
        var url = 'update_blog_url/';
        commonPostAjax(url, data, updateBlogUrlSuccess, updateBlogUrlFailure);
    });

    var updateBlogUrlSuccess = function(data) {
        console.log(data);
        clearErrorMsg();
        var param = data.url;
        var href_param = "/" + param + "/";
        $(".to_myblog a").attr("href", href_param);
        $("#id_url").text(param);
        $('p.update_blog_success_msg').text(data.message);
    }

    var updateBlogUrlFailure = function(xhr, status, errorThrown) {
        clearErrorMsg();
        if (xhr.responseJSON['url_error_msg']) {
            $('p.update_blog_url_error_msg').text(xhr.responseJSON['url_error_msg']);
        } else {
            $('p.update_blog_url_error_msg').text(xhr.responseJSON['message']);
        }
        $('p.update_blog_success_msg').text('');
    }


    $("#update_blog_all_btn").click(function(e) {
        console.log('update_blog_all_btn');
        e.preventDefault();
        var title = $("#id_title").val();
        var url = $("#id_url").val();
        var data = {
            'title': title,
            'url': url
        }
        $('#update_blog_confirm').modal('show');
        $('#update_blog_all_info_btn').click(function(){
            $('#update_blog_confirm').modal('hide');
            e.preventDefault();
            $('#update_confirm').modal('hide');
            var url = 'update_blog_info_all/';
            commonPostAjax(url, data, updateBlogInfoAllSuccess, updateBlogInfoAllFailure);
        });
    });

    var updateBlogInfoAllSuccess = function(data) {
        console.log(data);
        clearErrorMsg();
        var param = data.url
        var href_param = "/" + param + "/";
        $(".to_myblog a").attr("href", href_param);
        $("#id_url").text(param);
        $('p.update_blog_success_msg').text(data.message);
    }

    var updateBlogInfoAllFailure = function(xhr, status, errorThrown) {
        clearErrorMsg();
        var response = xhr.responseJSON;
        var keys = Object.keys(response);
        var errorList = [];
        keys.forEach(function(value) {
            if (value.match(/.*error_msg.*/)) {
                errorList.push(value);
            }
        });

        if (errorList.length != 0) {

            console.log(errorList);
            errorList.forEach(function(value) {
                target = "p.update_blog_" + value;
                console.log(target);
                $(target).text(xhr.responseJSON[value]);
            });
        } else {
            console.log(errorList);
            $('p.update_blog_info_all_error_msg').text(xhr.responseJSON['message']);
        }

        $('p.update_blog_success_msg').text('');
    }

    // $('.temp_select_btn').off();
    // $('.temp_select_btn').on('click', function(e){
    //     var obj = $(e.target);
    //     var temp_no = obj.data('temp-no');
    //     console.log(temp_no);
    //
    //
    //
    //     var url = ''
    //     var data = {
    //         temp_no : temp_no
    //     }
    //     commonPostAjax(url, data, selectTempSuccess);
    // })

    drawDesignTemp()
    tempChange();

    function drawDesignTemp(){
        var container = $(".temp_list");
        var temp_no = container.data('temp-no');
        var thema = container.find('[data-temp-no="'+ temp_no +'"]');
        thema.parents('.temp_select_wrap').addClass('temp_selected');
    }

    function tempChange(){
        var temp_no;

        $('.temp_select_btn').off();
        $('.temp_select_btn').on('click', function(e){
            var obj = $(e.target);
            var parent = obj.parents('.temp_select_wrap');
            temp_no = obj.data('temp-no');

            console.log(obj);
            console.log(parent);
            console.log(temp_no);
            $('.temp_selected').removeClass('temp_selected');
            parent.addClass('temp_selected');


        })

        $('.design_customize_submit_btn').on('click', function(e){
            var url = ''
            var data = {
                temp_no : temp_no
            }
            commonPostAjax(url, data, selectTempSuccess);
        })

    }

    function selectTempSuccess(data){
        console.log('テンプレートの選択に成功しました');
        location.reload();
    }

    function uuid() {
        var uuid = "", i, random;
        for (i = 0; i < 32; i++) {
            random = Math.random() * 16 | 0;

            if (i == 8 || i == 12 || i == 16 || i == 20) {
                uuid += "-"
            }
            uuid += (i == 12 ? 4 : (i == 16 ? (random & 3 | 8) : random)).toString(16);
        }
        return uuid;
    }
    console.log(document.cookie);

    if ($.cookie('uuId') == undefined) {
        console.log("uuid発行");
        var uuId = uuid();
        $.cookie('uuId', uuId);
        console.log("uuid:" + uuid());
        console.log($.cookie('uuId'));
    } else {
        console.log("uuidが既にある？");
        console.log($.cookie());
    }

    $('#id_thumbnail').on('change', function(e){
        var file = e.target.files[0];
        var blogUrl = window.URL.createObjectURL(file);
        $('#file_preview').attr('src', blogUrl);
    })

});
