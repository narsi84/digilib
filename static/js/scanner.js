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
		
		function init() {
			$scope.newbookName = '';
			$scope.newbookCategory = null;
			$scope.firstScan = true;
			$scope.currentScan = null;
			$scope.currentBookId = -1;
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

		$scope.scan = function(){
			if ($scope.firstScan){
				$http.get(API_URL + 'books/?name=' + $scope.newbookName)
					.then(function(response){
						if (response.data.results.length > 0) {
							$scope.bookExists = true;
							return;
						}
						else {
							$scope.bookExists = false;
							var payload = {
								'name': $scope.newbookName,
								'category': $scope.newbookCategory.description.id
								};
							$http.post(API_URL + 'books/', payload)
								.then(function(response){									
									$scope.currentBookId = response.data.id;
									
									$http.post(API_URL + 'startBook', {'bookid': $scope.currentBookId})
										.then(function(response){
											console.log(response);
											$scope.firstScan = false;
											performScan();									
										})
								})
						}
					})
			}
			else
				performScan();
		}
		
		function performScan(){
			$http.post(API_URL + 'scan', {'bookid': $scope.currentBookId})
				.then(function(response){
					$scope.currentScan = response.data.loc;
				})
		}
		
		$scope.finishBook = function(){
			
			$http.post(API_URL + 'stopBook', {'bookid': $scope.currentBookId})
				.then(function(response){
					init();
					console.log(response);	
					location.reload();						
				})
		}
	}]);
	
	
	
	
})(angular);
