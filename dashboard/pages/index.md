---
title: Welcome to Carbu-data
---

```sql prix_moyen_jour
SELECT
    p_maj_date,
    p_carburant,
    prix
FROM data.avg_prix
WHERE p_maj_date >= CURRENT_DATE - INTERVAL 90 DAYS
```
<LineChart 
    title='Evolution du prix moyen des carburants sur les 90 derniers jours'
    data={prix_moyen_jour}
    x=p_maj_date
    y=prix
    yAxisTitle="AVG Price per day"
    series=p_carburant
    handleMissing=connect
    yLog=true
    yFmt='#,##0.00€'
    yMin=.5
    chartAreaHeight=300
/>

```sql prix_jour
SELECT
    p_maj_date as date,
    s.nom,
    s.marque,
    s.ville,
    p_carburant as carburant,
    p_prix as prix
FROM data.prix_jour p
LEFT JOIN data.stations s
    ON p.s_id = s.id
```

```sql pivot_prix_jour
WITH r AS (
    SELECT
        s.nom AS Nom,
        s.marque AS Marque,
        s.ville AS Ville,
        p_carburant as carburant,
        p_prix as prix
    FROM data.prix_jour p
    LEFT JOIN data.stations s
        ON p.s_id = s.id
)
PIVOT r
ON carburant
USING FIRST(prix)
```

<DataTable
    title= 'Prix par station service (mis à jour sur les 3 derniers jours)'
    data={pivot_prix_jour}
    search=true
    rows=25
    rowNumbers=true
>
    <Column id=Marque /> 
    <Column id=Nom /> 
    <Column id=Ville /> 
    <Column id=E10 contentType=colorscale colorScale=negative fmt='#,##0.00€' /> 
    <Column id=E85 contentType=colorscale colorScale=negative fmt='#,##0.00€' /> 
    <Column id=GPLc contentType=colorscale colorScale=negative fmt='#,##0.00€' /> 
    <Column id=Gazole contentType=colorscale colorScale=negative fmt='#,##0.00€' /> 
    <Column id=SP95 contentType=colorscale colorScale=negative fmt='#,##0.00€' /> 
    <Column id=SP98 contentType=colorscale colorScale=negative fmt='#,##0.00€' /> 
</DataTable>


<DataTable
    title='Détail des prix et date de mise à jour'
    data={prix_jour}
    search=true
>
    <Column id=date /> 
    <Column id=nom /> 
    <Column id=marque /> 
    <Column id=ville /> 
    <Column id=carburant /> 
    <Column id=prix fmt='#,##0.00€' /> 
</DataTable>