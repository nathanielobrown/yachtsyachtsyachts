
function SearchTask(search_data) {
	$.extend(this, search_data);
}
SearchTask.prototype.test = function(){
	console.log('I extended someting with SearchTask');
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
			<img v-bind:src="result['image_url']" v-bind:title="result['image_hash']">
		</td>
		<td>{- result.title -}</td>
		<td>{- result['year'] -}</td>
		<td>{- result['location'] -}</td>
		<td>{- result['price'] -}</td>
		<td>\${- result.parsed_price|price -}</td>
		<!-- <td>{- result['currency'] -}</td> -->
		<td>
			<strong>View on:</strong>
			<ul>
				<li v-for="result in results">
					<a v-bind:href="result.link">{- result.link|domain_name -}</a>
				</li>
			</ul>
		</td>
	</tr>`

});

Vue.component('search-status', {
	props: ['status', 'note', 'num_results', 'domain'],
	computed:{
		title: function(){
			switch(this.status){
				case 'PENDING':
					return 'This search is queued.'
				case 'STARTED':
					return `${self.domain} is being searched.`
				case 'SUCCESS':
					switch(this.num_results){
						case 0:
							return 'No results found.'
						case 1:
							return 'Found 1 result.'
						default:
							return `Found ${this.num_results} results.`
					}
				case 'FAILURE':
					return `Something went wrong. This error has been reported.`
			}
		}
	},
	template: `
	<div v-bind:title="title" class="search_status">
		<div class="search_status_dot" v-bind:class="status">
			<template v-if="status=='FAILURE'">X</template>
			<template v-else-if="status=='SUCCESS'">{{ num_results }}</template>
		</div>
		{{ domain }}
	</div>
	`
})

var search = new Vue({
	el: 'main',
	delimiters: ['{-', '-}'],
	data: {
		manufacturer: "",
		length: "",
		result_groups: {},
		task_ids: [],
		searches: {},
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
			var groups = [];
			for(key in this.result_groups){
				if(this.result_groups.hasOwnProperty(key)){
					groups.push(this.result_groups[key]);
				}
			}
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
			this.result_groups = {};
			this.searches = {};
			this.has_searched = true;
			this.update_url();
			var qs = $.param({
				manufacturer:this.manufacturer,
				length:this.length
			});
			var url = '/search/?' + qs;
			console.log(url);
			var $promise = $.getJSON(url);
			$promise.success(function(resp){
				for(var i in resp.searches){
					var search = new SearchTask(resp.searches[i]);
					this.$set(this.$data.searches, search.task_id, search);
					this.$data.task_ids.push(search.task_id);
				}
				this.get_results(0);
			}.bind(this));
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
				for(var i in resp.searches){
					var search = resp.searches[i];
					// update search
					var old_search = this.searches[search.task_id];
					old_search.status = search.status;
					old_search.note = search.note;
					// old_search.num_results should always be zero
					if(search.num_results != old_search.num_results){
						// update results
						old_search.num_results = search.num_results;
						for(var i in search.results){
							var year = search.results[i].year
							if(typeof year  === "undefined"){
								// Random integer, so that we don't group all the
								// results with no year together
								year = Math.random().toString().slice(2);
							}
							var key = year + '_' + search.results[i].image_hash;
							if(this.$data.result_groups.hasOwnProperty(key)){
								this.$data.result_groups[key].push(search.results[i]);
							}else{
								this.$set(this.result_groups, key, [search.results[i]]);
							}
						}
					}
				}
				this.task_ids = resp.task_ids;
				this.get_results(errors);
			}.bind(this));
			$promise.fail(function(){
				this.get_results(errors + 1);
			}.bind(this));
		}
	}
});