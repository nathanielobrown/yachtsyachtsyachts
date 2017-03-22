// $(document).ready(function(){
// 	$('button[value="Search"]').on('click', function(e){
// 		results = [];
// 		e.preventDefault();
// 		var $form = $('form');
// 		var url = $form.prop('action') + '?' + $form.serialize();
// 		console.log(url);
// 		$.getJSON(url, function(resp){
// 			var task_ids = resp.task_ids;
// 			console.log(resp);
// 			get_result(task_ids);
// 		});
// 	});
// });

function get_result(task_ids){
	if(task_ids.length === 0){
		return
	}
	var $promise = $.ajax({
		url: '/search/results/',
		contentType: 'application/json',
		data: JSON.stringify({task_ids:task_ids}),
		method: 'POST'
	});
	$promise.success(function(resp){ console.log(resp)});
	$promise.error(function(resp){debugger});
}
function getParameterByName(name, url) {
    if (!url) {
      url = window.location.href;
    }
    name = name.replace(/[\[\]]/g, "\\$&");
    var regex = new RegExp("[?&]" + name + "(=([^&#]*)|&|#|$)"),
        results = regex.exec(url);
    if (!results) return null;
    if (!results[2]) return '';
    return decodeURIComponent(results[2].replace(/\+/g, " "));
}
Vue.filter('domain_name', function(url){
	var parser = document.createElement('a');
	parser.href = url;
	return parser.hostname;
});
Vue.filter('price', function(x){
	if(typeof x === 'undefined'){
		return "";
	}
    var parts = x.toString().split(".");
    parts[0] = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, ",");
    return parts[0];
});
Vue.component('result-group', {
	props: ['results'],
	delimiters: ['{-', '-}'],
	computed: {
		result: function() {
			return this.results[0];
		}
	},
	template: `
	<tr>
		<td>
			<img v-bind:src="result['image_url']">
		</td>
		<td>{- result.title -}</td>
		<td>{- result['year'] -}</td>
		<td>{- result['location'] -}</td>
		<td>{- result['price'] -}</td>
		<td>\${- result.parsed_price|price -}</td>
		<!-- <td>{- result['currency'] -}</td> -->
		<td>
			<ul>
				<li v-for="result in results">
					<a v-bind:href="result.link">{- result.link|domain_name -}</a>
				</li>
			</ul>
		</td>
	</tr>`

});

var search = new Vue({
	el: 'main',
	delimiters: ['{-', '-}'],
	data: {
		manufacturer: "",
		length: "",
		result_groups: {},
		task_ids: [],
		has_searched: false
	},
	created: function(){
		// show the page
		$('body').removeAttr('style');
		var manufacturer = getParameterByName('manufacturer');
		var length = getParameterByName('length');
		if(manufacturer && length){
			this.$data.manufacturer = manufacturer;
			this.$data.length = length;
			this.search();
		}
	},
	computed: {
		sorted_result_groups: function() {
			var groups = Object.values(this.result_groups);
			return groups.sort(function(a, b){
				return b[0].parsed_price - a[0].parsed_price;
			});
		}
	},
	methods: {
		update_url: function() {
			var qs = $.param({
				manufacturer: this.$data.manufacturer,
				length: this.$data.length
			});
			history.pushState({}, "", "/search/?"+qs);
		},
		search: function() {
			this.$data.result_groups = {};
			this.$data.has_searched = true;
			this.update_url();
			var qs = $.param({
				manufacturer:this.$data.manufacturer,
				length:this.$data.length
			});
			var url = '/search/?' + qs;
			console.log(url);
			var $promise = $.getJSON(url);
			$promise.success(function(resp){
				this.$data.task_ids = resp.task_ids;
				this.get_results(0);
			}.bind(this))
			;
		},
		get_results: function(errors) {
			if(this.$data.task_ids.length === 0){
				return;
			}
			if(errors > 2){
				console.log('To many errors with ' +
					        this.$data.task_ids.length + ' left.');
				return;
			}
			var $promise = $.ajax({
				url: '/search/results/',
				contentType: 'application/json',
				data: JSON.stringify({task_ids:this.$data.task_ids}),
				method: 'POST'
			});
			$promise.success(function(resp){
				for(var i in resp.results){
					var year = resp.results[i].year
					if(typeof year  === "undefined"){
						// Random integer, so that we don't group all the
						// results with no year together
						year = Math.random().toString().slice(2);
					}
					var key = year + '_' + resp.results[i].image_hash;
					if(this.$data.result_groups.hasOwnProperty(key)){
						this.$data.result_groups[key].push(resp.results[i]);
					}else{
						this.$set(this.result_groups, key, [resp.results[i]]);
					}
				}
				this.$data.task_ids = resp.task_ids;
				this.get_results(errors);
			}.bind(this));
			$promise.fail(function(){
				this.get_results(errors + 1);
			});
		}
	}
});
