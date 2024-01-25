function loadTableData() {
  var tablaElement = document.getElementById('tabla');
  var device = tablaElement.getAttribute('data-device');


  var domain = window.location.hostname;
  var port = window.location.port;

  var url = 'http://' + domain;
  if (port) {
    url += ':' + port;
  }
  url += '/show_users/' + device + '/get_users';

  return fetch(url)
    .then(response => response.json())
    .then(data => {
      console.log(data)
      return data['users'];
    })
    .catch(error => {
      console.error(error);
      return [];
    });
}

loadTableData()
  .then(tableData => {
    // Crear la tabla con los datos cargados
    var table = new Tabulator("#tabla", {
      data: tableData,
      layout: "fitColumns",
      pagination: "local",
      paginationSize: 50,
      paginationSizeSelector: [50, 100, 150],
      columns: [
        {title: "Usuario num.", field: "employeeNo", headerFilter:true},
        {title: "Nombre", field: "name", headerFilter:true},
        {title: "Género", field: "gender", headerFilter:true},
        {title: "Habilitado", field: "Valid.enable", headerFilter: true},
        {title: "Inicio", field: "Valid.beginTime", headerFilter:true},
        {title: "Final", field: "Valid.endTime", headerFilter:true},
        {title: "Tipo de usuario", field: "userType", headerFilter:true}
      ],
      initialSort: [
        {column: "employeeNo", dir: "asc"}
      ],
      rowFormatter: function(row){
        var index = row.getPosition(true);
        if(index % 2 === 0){
          row.getElement().classList.add("even");
        }else{
          row.getElement().classList.add("odd");
        }
      },
    });
  });
