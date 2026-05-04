---
title: Welcome to Evidence
---

<Details title='How to edit this page'>

  This page can be found in your project at `/pages/index.md`. Make a change to the markdown file and save it to see the change take effect in your browser.
</Details>

```sql prix_moyen_jour
SELECT
    p_maj_date,
    p_carburant,
    prix
FROM data.avg_prix
WHERE p_maj_date >= CURRENT_DATE - INTERVAL 90 DAYS
```
<LineChart 
    data={prix_moyen_jour}
    x=p_maj_date
    y=prix
    yAxisTitle="AVG Price per day"
    series=p_carburant
    handleMissing=connect
    yLog=true
    yMin=.5
    chartAreaHeight=500
/>

```sql prix_moyen_mois
SELECT
    strftime(p_maj_date, '%Y-%m') AS mois,
    p_carburant,
    AVG(prix) as prix
FROM data.avg_prix
GROUP BY mois, p_carburant
ORDER BY mois
```

<Heatmap
    data={prix_moyen_mois}
    x=mois
    y=p_carburant
    value=prix
    xLabelRotation=-45
    rightPadding=40
    colorScale={[
        ['rgb(254,234,159)', 'rgb(254,234,159)'],
        ['rgb(218,66,41)', 'rgb(218,66,41)']
    ]}
/>

<!-- -- ```sql cp
-- SELECT DISTINCT cp
-- FROM data.stations
-- ``` -->

<!-- -- <Dropdown
--     name=cp
--     data={cp}
--     title="Code postal"
--     value=cp
-- /> -->

<TextInput
    name=cp
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
WHERE s.cp like '${inputs.cp}%'
```
<DataTable
    data={prix_jour}
/>