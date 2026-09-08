# VRP Streamlit - Dynamic Input

Prototype VRP dengan input manual dan fitur:
- Nama lokasi
- Demand
- **Node Type: Mandatory / Optional**
- Distance Matrix
- Time Matrix
- Jumlah kendaraan
- Kapasitas kendaraan
- Depot
- Algoritma
- **Cost calculation**: fixed cost kendaraan, cost per distance, cost per time, dan penalty Optional Node yang dilewati

## Aturan Mandatory / Optional

- **Mandatory**: node wajib dikunjungi. Constraint Programming tidak memberikan opsi drop.
- **Optional**: node boleh tidak dikunjungi. Pada Constraint Programming node dibuat sebagai disjunction dengan penalty drop.
- Depot selalu diperlakukan sebagai Mandatory.
- Heuristik Nearest Neighbor dan Nearest Insert berusaha melayani semua Mandatory Node dan Optional Node yang masih feasible terhadap kapasitas.

## Perhitungan Cost

`Total Cost = (Total Distance × Cost/Distance) + (Total Time × Cost/Time) + (Jumlah kendaraan aktif × Fixed Cost/Kendaraan) + (Optional Node dilewati × Drop Penalty)`

Objective `Distance` atau `Time` tetap digunakan untuk menentukan rute, sedangkan **Total Cost** dihitung terpisah menggunakan konfigurasi cost.

## Run

```bash
pip install -r requirements.txt
streamlit run app.py
```
