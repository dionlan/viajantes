import { Routes } from '@angular/router';
import { FlightSearchComponent } from './flight-search/flight-search.component';

export const routes: Routes = [
  {
    path: '',
    component: FlightSearchComponent,
    title: 'Pesquisa de Voos'
  },
];