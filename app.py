from pathlib import Path
import math,json
import pandas as pd,numpy as np,streamlit as st,plotly.graph_objects as go,plotly.express as px
P=Path(__file__).parent/'data';L=pd.read_csv(P/'locations.csv');D=pd.read_csv(P/'dimensions.csv');Q=pd.read_csv(P/'quality_report.csv');R=pd.read_csv(P/'relationships.csv');K=D.dimension_key.tolist();LAB=dict(zip(D.dimension_key,D.label))
THEMES={'Home & value':['housing_cost','housing_choice'],'Everyday life':['daily_services','healthcare','digital'],'Connections':['rail','road','airport','family_network'],'Outdoors':['walking','greenspace','waterside','climate','terrain'],'Culture & community':['food','culture','learning','community'],'Character & future':['heritage','independence','pace','safety','future_fit']};MODE={'Car':(35,10),'Rail':(50,25),'Mixed':(40,20)}
st.set_page_config(page_title='Location Lifestyle AI V7',page_icon='🧭',layout='wide');st.markdown('''<style>.block-container{padding-top:1.1rem}.hero{padding:1.25rem 1.55rem;border-radius:20px;background:linear-gradient(120deg,#10372b,#527c67);color:white}.brief{padding:1rem 1.2rem;border-left:6px solid #dba641;background:#f7faf8;border-radius:12px}.note{font-size:.88rem;color:#596a61}</style>''',unsafe_allow_html=True)
if 'weights' not in st.session_state:st.session_state.weights={'Home & value':6,'Everyday life':8,'Connections':9,'Outdoors':9,'Culture & community':9,'Character & future':8}
if 'network' not in st.session_state:st.session_state.network=pd.DataFrame([{'Place':'St Albans','Category':'Family','Importance':10,'Visits/month':4.0,'Mode':'Car'},{'Place':'Marlow','Category':'Home / friends','Importance':7,'Visits/month':2.0,'Mode':'Car'}])
def miles(a,b,c,d):
 z=math.sin(math.radians(c-a)/2)**2+math.cos(math.radians(a))*math.cos(math.radians(c))*math.sin(math.radians(d-b)/2)**2;return 3958.8*2*math.asin(math.sqrt(z))
def journey(mi,mode):mph,over=MODE[mode];return over+60*mi/mph
def network_rows(r):
 rows=[]
 for _,n in st.session_state.network.iterrows():
  h=L[L.name==n.Place]
  if h.empty:continue
  mi=miles(r.latitude,r.longitude,h.iloc[0].latitude,h.iloc[0].longitude);mins=journey(mi,n.Mode);monthly=2*mins*float(n['Visits/month'])/60;score=max(0,100-mins/3)
  rows.append({'Place':n.Place,'Category':n.Category,'Importance':float(n.Importance),'Visits/month':float(n['Visits/month']),'Mode':n.Mode,'Miles':mi,'One-way minutes':mins,'Monthly hours':monthly,'Node score':score,'lat':h.iloc[0].latitude,'lon':h.iloc[0].longitude})
 return pd.DataFrame(rows)
def nscore(r):
 z=network_rows(r)
 if z.empty:return 75
 return float(np.average(z['Node score'],weights=z.Importance*np.maximum(z['Visits/month'],.25)))
def score():
 ww={k:st.session_state.weights[t] for t,ks in THEMES.items() for k in ks};w=np.array([ww[k] for k in K]);o=L.copy();o['Lifestyle']=o[K].to_numpy()@w/(10*w.sum())*100;o['Life Network']=o.apply(nscore,axis=1);o['Balanced']=.60*o.Lifestyle+.40*o['Life Network'];return o.sort_values(['Balanced','importance_rank'],ascending=[False,True]),ww
def gauge(v,title):
 f=go.Figure(go.Indicator(mode='gauge+number',value=v,title={'text':title},gauge={'axis':{'range':[0,100]},'bar':{'color':'#2d6a51'},'steps':[{'range':[0,45],'color':'#f2d0c9'},{'range':[45,70],'color':'#f1dfae'},{'range':[70,100],'color':'#acd1bd'}]}));f.update_layout(height=180,margin=dict(l=15,r=15,t=40,b=5));return f
def lines_map(candidate,z):
 f=go.Figure();f.add_trace(go.Scattergeo(lon=[candidate.longitude],lat=[candidate.latitude],mode='markers+text',text=[candidate['name']],textposition='top center',marker=dict(size=21,color='#173f33',symbol='star'),name='Candidate'))
 for _,r in z.iterrows():
  col='#33965d' if r['One-way minutes']<=60 else '#dda337' if r['One-way minutes']<=120 else '#c95045';f.add_trace(go.Scattergeo(lon=[candidate.longitude,r.lon],lat=[candidate.latitude,r.lat],mode='lines',line=dict(color=col,width=1.5+3*r.Importance/10),text=f"{r.Place}: {r.Miles:.0f} miles, {r['One-way minutes']:.0f} min, {r['Monthly hours']:.1f} h/month",hoverinfo='text',showlegend=False));f.add_trace(go.Scattergeo(lon=[r.lon],lat=[r.lat],mode='markers+text',text=[r.Place],textposition='top center',marker=dict(size=8+r.Importance,color=col),name=r.Place))
 f.update_geos(scope='europe',fitbounds='locations',showland=True,landcolor='#edf2ee');f.update_layout(height=500,margin=dict(l=0,r=0,t=0,b=0));return f
st.markdown('<div class="hero"><h1>🧭 Location Lifestyle AI V7</h1><p>Lifestyle fit, Life Network and the real monthly burden of staying connected.</p></div>',unsafe_allow_html=True)
with st.sidebar:
 current=st.selectbox('Current location',L.name,index=int(L.index[L.name=='Marlow'][0]));st.header('Tune your next chapter')
 for t in THEMES:st.session_state.weights[t]=st.slider(t,0,10,st.session_state.weights[t],key=t)
 st.download_button('Download profile',json.dumps({'current':current,'weights':st.session_state.weights,'life_network':st.session_state.network.to_dict('records')},indent=2),'profile_v7.json','application/json',use_container_width=True)
out,W=score();base=out[out.name==current].iloc[0];base_hours=network_rows(base)['Monthly hours'].sum();focus=sorted(st.session_state.weights,key=st.session_state.weights.get,reverse=True)[:3]
st.markdown(f'<div class="brief">You are seeking a place led by <b>{focus[0].lower()}, {focus[1].lower()} and {focus[2].lower()}</b>. V7 balances lifestyle fit (60%) with Life Network (40%), and translates network choices into estimated miles, journey minutes and monthly return-travel hours.</div>',unsafe_allow_html=True)
tabs=st.tabs(['Dashboard','Recommendations','Life Network','Gravity heat map','Travel burden','Compare','Place conversation','AI conversation','Data quality'])
with tabs[0]:
 a,b,c,d=st.columns(4);a.metric('Named places',len(L));b.metric('Network nodes',len(st.session_state.network));c.metric('Current lifestyle',f"{base.Lifestyle:.0f}");d.metric('Current network',f"{base['Life Network']:.0f}")
 cs=st.columns(3)
 for i,(t,v) in enumerate(st.session_state.weights.items()):cs[i%3].plotly_chart(gauge(v*10,t),use_container_width=True,key='g'+t)
with tabs[1]:
 n=st.slider('Shortlist',5,25,12);reg=st.multiselect('Regions',sorted(L.region.unique()),default=sorted(L.region.unique()));x=out[(out.name!=current)&out.region.isin(reg)].head(n).copy();x['Monthly hours']=x.apply(lambda r:network_rows(r)['Monthly hours'].sum(),axis=1);x['Δ hours']=x['Monthly hours']-base_hours;x['Why']=x.apply(lambda r:', '.join(LAB[k] for k in sorted(K,key=lambda k:r[k]*W[k],reverse=True)[:3]),axis=1)
 st.dataframe(x[['name','county_area','Lifestyle','Life Network','Balanced','Monthly hours','Δ hours','Why']].style.format({'Lifestyle':'{:.1f}','Life Network':'{:.1f}','Balanced':'{:.1f}','Monthly hours':'{:.1f}','Δ hours':'{:+.1f}'}),hide_index=True,use_container_width=True);st.scatter_chart(x,x='Lifestyle',y='Life Network',color='region',size='Balanced')
with tabs[2]:
 st.subheader('The places and people that anchor your life');e=st.data_editor(st.session_state.network,num_rows='dynamic',use_container_width=True,column_config={'Place':st.column_config.SelectboxColumn(options=L.name.tolist()),'Category':st.column_config.SelectboxColumn(options=['Family','Friends','Home / friends','Travel','Healthcare','Culture','Other']),'Importance':st.column_config.NumberColumn(min_value=1,max_value=10),'Visits/month':st.column_config.NumberColumn(min_value=.1,max_value=30.,step=.5),'Mode':st.column_config.SelectboxColumn(options=list(MODE))})
 if st.button('Apply Life Network',type='primary'):st.session_state.network=e;st.rerun()
 cand=st.selectbox('Candidate journey view',out.name);r=out[out.name==cand].iloc[0];z=network_rows(r);st.plotly_chart(lines_map(r,z),use_container_width=True);st.caption('Green ≤ 60 estimated minutes; amber 61–120; red > 120. Line thickness and marker size reflect importance.')
with tabs[3]:
 st.subheader('Network gravity across the catalogue');metric=st.radio('Map layer',['Life Network Score','Opportunity: lifestyle gain minus network penalty'],horizontal=True)
 heat=out.copy();heat['Lifestyle gain']=heat.Lifestyle-base.Lifestyle;heat['Network penalty']=base['Life Network']-heat['Life Network'];heat['Opportunity']=heat['Lifestyle gain']-heat['Network penalty']
 colour='Life Network' if metric.startswith('Life') else 'Opportunity';fig=px.scatter_geo(heat,lat='latitude',lon='longitude',color=colour,size='Balanced',hover_name='name',hover_data={'county_area':True,'Lifestyle':':.1f','Life Network':':.1f','Opportunity':':+.1f','latitude':False,'longitude':False},scope='europe',color_continuous_scale='RdYlGn');fig.update_geos(fitbounds='locations',showland=True,landcolor='#edf2ee');fig.update_layout(height=620,margin=dict(l=0,r=0,t=15,b=0));st.plotly_chart(fig,use_container_width=True);st.caption('This is a catalogue-point gravity map rather than a continuous drive-time isochrone. Lower-precision coordinate rows are identified in the database.')
with tabs[4]:
 cand2=st.selectbox('Candidate',out.name,key='burden');r=out[out.name==cand2].iloc[0];z=network_rows(r);total=z['Monthly hours'].sum();a,b,c=st.columns(3);a.metric('Monthly return travel',f'{total:.1f} h');b.metric(f'Change vs {current}',f'{total-base_hours:+.1f} h');c.metric('Life Network score',f"{r['Life Network']:.0f}");st.dataframe(z[['Place','Category','Mode','Importance','Visits/month','Miles','One-way minutes','Monthly hours','Node score']].style.format({'Miles':'{:.1f}','One-way minutes':'{:.0f}','Monthly hours':'{:.1f}','Node score':'{:.0f}'}),hide_index=True,use_container_width=True);st.bar_chart(z.set_index('Place')['Monthly hours']);st.warning('Estimates use effective speeds of 35 mph by car, 50 mph by rail and 40 mph mixed, plus mode overhead. They are not routes, traffic or timetables.')
with tabs[5]:
 choices=st.multiselect('Compare 2–4',L.name,default=['Marlow','Winchester','Stamford'],max_selections=4)
 if len(choices)>1:
  c=out[out.name.isin(choices)].set_index('name').copy();c['Monthly hours']=[network_rows(r)['Monthly hours'].sum() for _,r in c.iterrows()];st.dataframe(c[['Lifestyle','Life Network','Balanced','Monthly hours','county_area','region']].T,use_container_width=True);st.bar_chart(c[['Lifestyle','Life Network','Balanced']])
with tabs[6]:
 name=st.selectbox('Discuss a place',out.name);r=out[out.name==name].iloc[0];drivers=sorted(K,key=lambda k:r[k]*W[k],reverse=True);hours=network_rows(r)['Monthly hours'].sum();st.subheader(f"{r['name']} · {r['county_area']} · {r['region']}");a,b,c=st.columns(3);a.plotly_chart(gauge(r.Lifestyle,'Lifestyle'),use_container_width=True);b.plotly_chart(gauge(r['Life Network'],'Life Network'),use_container_width=True);c.plotly_chart(gauge(r.Balanced,'Balanced'),use_container_width=True);st.markdown(f"For this profile, **{LAB[drivers[0]]}**, **{LAB[drivers[1]]}** and **{LAB[drivers[2]]}** are the strongest match drivers. The estimated network burden is **{hours:.1f} return-travel hours per month**, **{hours-base_hours:+.1f} hours versus {current}**. The first validation questions should cover the lowest-weighted match areas and whether the estimated network journeys remain acceptable in real traffic and rail conditions.")
with tabs[7]:
 st.write('Ask for a grounded comparison or next-chapter view. AI is optional and receives only the selected profile, candidate metrics and visible caveats.')
 question=st.text_area('Question',f'Would moving from {current} to Winchester realistically improve our lifestyle without making family travel too burdensome?')
 ai_place=st.selectbox('Candidate context',out.name,key='aiplace')
 if st.button('Ask AI'):
  try:
   from openai import OpenAI
   key=st.secrets.get('OPENAI_API_KEY','')
   if not key:st.warning('Add OPENAI_API_KEY to Streamlit Secrets.')
   else:
    r=out[out.name==ai_place].iloc[0];z=network_rows(r);context={'candidate':ai_place,'current':current,'lifestyle':round(r.Lifestyle,1),'life_network':round(r['Life Network'],1),'balanced':round(r.Balanced,1),'monthly_hours':round(z['Monthly hours'].sum(),1),'delta_hours':round(z['Monthly hours'].sum()-base_hours,1),'weights':st.session_state.weights,'travel_model':'estimated; miles; 35 mph car, 50 mph rail, 40 mph mixed; not live routing'}
    prompt='Answer as a thoughtful UK relocation analyst. Use only this JSON and the user question. Separate evidence from judgement. Mention that travel is estimated, not live. JSON: '+json.dumps(context)+'\nQuestion: '+question
    res=OpenAI(api_key=key).responses.create(model=st.secrets.get('OPENAI_MODEL','gpt-4.1-mini'),input=prompt);st.markdown(res.output_text)
  except Exception as e:st.error(f'AI unavailable: {e}')
with tabs[8]:
 a,b,c=st.columns(3);a.metric('Catalogue rows',len(L));b.metric('QA checks passed',int((Q.result=='PASS').sum()));c.metric('Core coordinates',int((L.coordinate_precision=='rounded_town_centre').sum()));st.dataframe(Q,hide_index=True,use_container_width=True);st.dataframe(L[['name','county_area','region','importance_tier','verification_status','coordinate_precision']],hide_index=True,use_container_width=True);st.download_button('Download catalogue',L.to_csv(index=False),'locations_v7.csv','text/csv');st.warning('County/area membership is curated. Core coordinates are rounded town centres; expansion rows marked regional_seed_point require authoritative geocoding before real-world journey decisions.')
