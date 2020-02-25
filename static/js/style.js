$(function(){

	// ハンバーガーメニュー表示・非表示
	$("#open_btn").click(function(){
		$("#nav_contents").addClass("open");
	});
	$("#close_btn").click(function(){
		$("#nav_contents").removeClass("open");
	});

	$(".is_public_btn").click(function(){
		var obj = $(this);
		var val = obj.html();

		if (val == "公開する") {
			obj.html("非公開");
			obj.addClass('btn-dark');
			obj.removeClass('btn-info');
		} else {
			obj.html("公開する");
			obj.addClass('btn-info');
			obj.removeClass('btn-dark');
		}
	});

	// コメント詳細モーダル表示
	$('.detail_comment_btn').click(function(){

		var comment_no = $(this).val();
		var comment_content = $('[comment_pk="' + comment_no + '"]');
		console.log(comment_content);

		var comment_name = comment_content.find('.comment_name').html();
		var comment_text = comment_content.find('.comment_text').html();
		var comment_email = comment_content.find('.comment_email').html();
		var comment_created_at = comment_content.find('.comment_created_at').html();
		var comment_is_public = comment_content.find('.comment_is_public').html();

		$('#detail_comment .detail_comment_name').html(comment_name);
		$('#detail_comment .detail_comment_text').html(comment_text);
		$('#detail_comment .detail_comment_email').html(comment_email);
		$('#detail_comment .detail_comment_created_at').html(comment_created_at);
		$('#detail_comment .detail_comment_is_public').html(comment_is_public);

		$('#detail_comment').modal('show');
	});

})
