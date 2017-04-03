(function(angular) {
	'use strict';
	
	var app = angular.module('scanner', []);
	
	var ORIGIN = window.location.origin;
	var API_URL = ORIGIN + ':8000/api/v1/';
	
	app.config(function($httpProvider) {
		$httpProvider.defaults.xsrfCookieName = 'csrftoken';
		$httpProvider.defaults.xsrfHeaderName = 'X-CSRFToken';	
	})
	
	app.controller('libraryController', ['$http', '$scope', function($http, $scope){
		$scope.library = [];
		$scope.socket = new WebSocket("ws://" + window.location.host + ":8000/chat/");						

		// var viewer = ImageViewer('#scanview');
		
		function init() {
			$scope.newbookName = '';
			$scope.newbookCategory = null;
			$scope.newbookAuthor = '';
			$scope.currentScan = null;
			$scope.currentBookId = -1;
			$scope.scanType = 0;
		};
		
		init();
		$http.get(API_URL + 'categories')
			.then(function(response){
				var categories = response.data.results;

				angular.forEach(categories, function(category, i){
					var cat_books = {'description': category};
					$http.get(API_URL + 'books/?category=' + category.id)
						.then(function(response){
							var books = response.data.results;
							cat_books['books'] = books;
							console.log(books);
						})
					$scope.library.push(cat_books);						
				});	
			})

		$scope.createBook = function() {
			$http.get(API_URL + 'books/?name=' + $scope.newbookName)
				.then(function(response){
					if (response.data.results.length > 0) {
						$scope.bookExists = true;
						$scope.tmpbookName = $scope.newbookName;
						$scope.newbookName = '';
						return;
					}
					else {
						$scope.bookExists = false;
						var payload = {
							'name': $scope.newbookName,
							'category': $scope.newbookCategory,
							'author': $scope.newbookAuthor
							};
						$http.post(API_URL + 'createBook', payload)
							.then(function(response){									
								$scope.currentBookId = response.data.bookid;
								
								$http.post(API_URL + 'startBook', {'bookid': $scope.currentBookId})
									.then(function(response){
										console.log(response);
										$('#newbookModal').modal('hide');
										$('#scanModal').modal('show');
									})

							})
					}
				})
		}

		$scope.test = function() {
			if ($scope.scantimer) {
				clearInterval($scope.scantimer);
				$scope.scantimer = null;
			}
			else
				// $scope.scantimer = setInterval(function(){console.log("Testing")}, 2000);		
			$scope.scantimer = setInterval(pollscan, 5000);
		}

		$scope.scan = function (){
			$http.post(API_URL + 'scan', {'bookid': $scope.currentBookId})
				.then(function(response){
					$scope.currentScan = response.data;
					console.log(response.data);
				})
		}

		$scope.autoScan = function(){
			$scope.socket.send(JSON.stringify({msg: "begin_auto"}));
		}
				
		$scope.finishBook = function(){
			if (!$scope.currentBookId) {
				alert("Scan not started")
				return;
			}

			$http.post(API_URL + 'stopBook', {'bookid': $scope.currentBookId})
				.then(function(response){
					init();
					console.log(response);	
					location.reload();						
				})
		}

		$scope.selectAction = function(curr_action){
			curr_action.active = !curr_action.active;

			angular.forEach($scope.actions, function(action, i){
				if (curr_action == action)
					return 1;

				if (!curr_action.active) {
					action.enabled = true;
				}
				else {
					action.enabled = false;
					action.active = false;
				}
			})

			curr_action.method();
		}

		$scope.socket.onmessage = function(e) {
			var data = JSON.parse(e.data)
			$scope.currentScan = data.url;
		}

		$scope.socket.onopen = function() {
		    $scope.socket.send(JSON.stringify({msg: 'initiate_handshake'}));
		}

		$scope.closeAlert = function(){
		}

		function pollscan(){
			$http.post(API_URL + 'test')
				.then(function(response){
					$scope.currentScan = response.data;
				})				
		}					

		$scope.actions = {
			test: {label: 'Test', method: $scope.test, active: false, enabled: true, icon: 'glyphicon-cog'},
			single: {label: 'Single Scan', method: $scope.scan, active: false, enabled: true, icon: 'glyphicon-screenshot'},
			auto: {label: 'Auto Scan', method: $scope.autoScan, active: false, enabled: true, icon: 'glyphicon-play-circle'},
			finish: {label: 'Finish', method: $scope.finishBook, active: false, enabled: true, icon: 'glyphicon-check'},
		}

	}]);
	
})(angular);
