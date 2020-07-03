jQuery( document ).ready(function( ) {
	var urlArray = window.location.href.split('/');
	urlArray.pop(); // Remove space
	urlArray.pop(); // Remove "new"
	var url = urlArray.join('/');
	$("#cancelButton").attr("href", url);
});
