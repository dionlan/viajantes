// src/app/services/flight.service.ts
import { Injectable } from '@angular/core';
import { delay, Observable, of } from 'rxjs';
import { FlightSearchParams, FlightSearchResponse, MOCK_FLIGHTS } from '../model/flight-data';

@Injectable({
    providedIn: 'root'
})
export class FlightService {
    private mockFlights = MOCK_FLIGHTS;

    searchFlights(params: FlightSearchParams): Observable<FlightSearchResponse> {
        // Converta as datas para strings ISO se forem objetos Date
        const departureDateStr = params.departureDate instanceof Date
            ? params.departureDate.toISOString()
            : params.departureDate;

        const returnDateStr = params.returnDate instanceof Date
            ? params.returnDate.toISOString()
            : params.returnDate;

        // Filtra os voos conforme os parâmetros
        const filteredFlights = this.mockFlights.filter(flight => {
            const originMatch = flight.origin.code === params.origin ||
                flight.origin.city.toLowerCase().includes(params.origin.toLowerCase());

            const destinationMatch = flight.destination.code === params.destination ||
                flight.destination.city.toLowerCase().includes(params.destination.toLowerCase());

            const flightDate = new Date(flight.departure);
            const searchDate = departureDateStr ? new Date(departureDateStr) : null;

            const dateMatch = searchDate
                ? flightDate.toDateString() === searchDate.toDateString()
                : true;

            const classMatch = flight.cabinClass === params.cabinClass;
            const seatsMatch = flight.seatsAvailable >= params.passengers;

            return originMatch && destinationMatch && dateMatch && classMatch && seatsMatch;
        });

        // Simula resposta da API com delay
        return of({
            success: true,
            data: filteredFlights,
            message: filteredFlights.length > 0 ?
                `${filteredFlights.length} voos encontrados` :
                'Nenhum voo encontrado para os critérios selecionados'
        }).pipe(delay(500));
    }

    getFlightById(id: string) {
        const flight = this.mockFlights.find(f => f.id === id);
        return of({
            success: !!flight,
            data: flight || null,
            message: flight ? 'Voo encontrado' : 'Voo não encontrado'
        }).pipe(delay(300));
    }
}