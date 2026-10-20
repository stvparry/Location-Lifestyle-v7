from pathlib import Path
import io,math,json,textwrap
import pandas as pd,numpy as np,streamlit as st,plotly.graph_objects as go,plotly.express as px
P=Path(__file__).parent/'data';need=['locations.csv','dimensions.csv','quality_report.csv','relationships.csv'];missing=[x for x in need if not (P/x).exists()]
if missing:st.error('Keep the V7 data folder in this repository. Missing: '+', '.join(missing));st.stop()
L=pd.read_csv(P/'locations.csv');D=pd.read_csv(P/'dimensions.csv');Q=pd.read_csv(P/'quality_report.csv');K=D.dimension_key.tolist();LAB=dict(zip(D.dimension_key,D.label))
THEMES={'Home & value':['housing_cost','housing_choice'],'Everyday life':['daily_services','healthcare','digital'],'Connections':['rail','road','airport','family_network'],'Outdoors':['walking','greenspace','waterside','climate','terrain'],'Culture & community':['food','culture','learning','community'],'Character & future':['heritage','independence','pace','safety','future_fit']};MODE={'Car':(35,10),'Rail':(50,25),'Mixed':(40,20)}
PRESETS={'Stephen & Julie':{'household':'Retired couple','budget':'£1m–£2m','horizon':'3–8 years','notes':'Restaurants, walking, culture, travel and staying close to family. Character without isolation.','weights':{'Home & value':6,'Everyday life':8,'Connections':10,'Outdoors':9,'Culture & community':9,'Character & future':8}},'Active coastal next chapter':{'household':'Retired couple','budget':'£750k–£1m','horizon':'0–3 years','notes':'Coast, walking, community and year-round life matter most.','weights':{'Home & value':6,'Everyday life':7,'Connections':6,'Outdoors':10,'Culture & community':8,'Character & future':9}},'Connected culture':{'household':'Couple','budget':'£1m–£2m','horizon':'3–8 years','notes':'Culture, food, learning and good access to family and transport.','weights':{'Home & value':5,'Everyday life':8,'Connections':10,'Outdoors':6,'Culture & community':10,'Character & future':8}}}
st.set_page_config(page_title='Location Lifestyle AI V7.1',page_icon='🧭',layout='wide');st.markdown('''<style>.block-container{padding-top:1rem}.hero{padding:1.15rem 1.5rem;border-radius:18px;background:linear-gradient(120deg,#10372b,#527c67);color:white}.brief{padding:.9rem 1.1rem;border-left:6px solid #dba641;background:#f7faf8;border-radius:12px}.compact-note{font-size:.86rem;color:#5a6b62}.stTabs [data-baseweb="tab"]{font-size:.92rem}</style>''',unsafe_allow_html=True)
if 'profile' not in st.session_state:st.session_state.profile=PRESETS['Stephen & Julie'].copy()
if 'network' not in st.session_state:st.session_state.network=pd.DataFrame([{'Remove':False,'Place':'St Albans','Category':'Family','Importance':10,'Visits/month':4.0,'Mode':'Car'},{'Remove':False,'Place':'Marlow','Category':'Home / friends','Importance':7,'Visits/month':2.0,'Mode':'Car'}])
if 'network_floor' not in st.session_state:st.session_state.network_floor=58
def miles(a,b,c,d):
 z=math.sin(math.radians(c-a)/2)**2+math.cos(math.radians(a))*math.cos(math.radians(c))*math.sin(math.radians(d-b)/2)**2;return 7917.6*math.asin(math.sqrt(z))
def bearing(a,b,c,d):
 p1,p2=math.radians(a),math.radians(c);dl=math.radians(d-b);y=math.sin(dl)*math.cos(p2);x=math.cos(p1)*math.sin(p2)-math.sin(p1)*math.cos(p2)*math.cos(dl);return (math.degrees(math.atan2(y,x))+360)%360
def journey(mi,mode):mph,over=MODE[mode];return over+60*mi/mph
def nrows(r):
 rows=[]
 for _,n in st.session_state.network.iterrows():
  h=L[L.name==n.Place]
  if h.empty:continue
  mi=miles(r.latitude,r.longitude,h.iloc[0].latitude,h.iloc[0].longitude);mins=journey(mi,n.Mode);monthly=2*mins*float(n['Visits/month'])/60
  rows.append({'Place':n.Place,'Category':n.Category,'Importance':float(n.Importance),'Visits/month':float(n['Visits/month']),'Mode':n.Mode,'Miles':mi,'One-way minutes':mins,'Monthly hours':monthly,'Node score':max(0,100-mins/3),'Bearing':bearing(r.latitude,r.longitude,h.iloc[0].latitude,h.iloc[0].longitude)})
 return pd.DataFrame(rows)
def ns(r):
 z=nrows(r)
 return 75 if z.empty else float(np.average(z['Node score'],weights=z.Importance*np.maximum(z['Visits/month'],.25)))
def score():
 ww={k:st.session_state.profile['weights'][t] for t,ks in THEMES.items() for k in ks};w=np.array([ww[k] for k in K]);o=L.copy();o['Lifestyle']=o[K].to_numpy()@w/(10*w.sum())*100;o['Life Network']=o.apply(ns,axis=1);o['Balanced']=.55*o.Lifestyle+.45*o['Life Network'];return o.sort_values(['Balanced','importance_rank'],ascending=[False,True]),ww
def gauge(v,title,key):
 title='<br>'.join(textwrap.wrap(title,16));f=go.Figure(go.Indicator(mode='gauge+number',value=v,title={'text':title,'font':{'size':12}},number={'font':{'size':22}},gauge={'axis':{'range':[0,100],'tickfont':{'size':8}},'bar':{'color':'#2d6a51'},'steps':[{'range':[0,45],'color':'#f2d0c9'},{'range':[45,70],'color':'#f1dfae'},{'range':[70,100],'color':'#acd1bd'}]}));f.update_layout(height=145,margin=dict(l=8,r=8,t=38,b=3));st.plotly_chart(f,use_container_width=True,key=key)
def radial(r,z):
 f=go.Figure();f.add_trace(go.Scatter(x=[0],y=[0],mode='markers+text',text=[r['name']],textposition='top center',marker=dict(size=28,color='#163e32',symbol='star'),name='Candidate'))
 maxm=max(z.Miles.max() if len(z) else 1,1)
 for _,n in z.iterrows():
  rad=1.4+4.8*math.sqrt(n.Miles/maxm);ang=math.radians(90-n.Bearing);x,y=rad*math.cos(ang),rad*math.sin(ang);colour='#32965d' if n['One-way minutes']<=60 else '#dfa43a' if n['One-way minutes']<=120 else '#c95045';edge=f"{n.Miles:.0f} miles · {n['One-way minutes']:.0f} min<br>{n['Monthly hours']:.1f} h/month"
  f.add_trace(go.Scatter(x=[0,x],y=[0,y],mode='lines+text',text=['',edge],textposition='middle center',line=dict(color=colour,width=2+3*n.Importance/10),hoverinfo='text',hovertext=['',f"{n.Place}<br>{edge}"],showlegend=False));f.add_trace(go.Scatter(x=[x],y=[y],mode='markers+text',text=[n.Place],textposition='top center',marker=dict(size=11+n.Importance,color=colour),name=n.Place,hovertext=f"{n.Category}<br>{edge}"))
 f.update_xaxes(visible=False,range=[-7,7]);f.update_yaxes(visible=False,range=[-7,7],scaleanchor='x');f.update_layout(height=610,margin=dict(l=5,r=5,t=20,b=5),plot_bgcolor='#f7faf8',showlegend=False);return f
st.markdown('<div class="hero"><h1>🧭 Location Lifestyle AI V7.1</h1><p>A clearer profile, a stricter shortlist and a candidate-centred Life Network.</p></div>',unsafe_allow_html=True)
with st.sidebar:
 st.header('Household profile');preset=st.selectbox('Preset',PRESETS)
 if st.button('Load preset',use_container_width=True):st.session_state.profile=json.loads(json.dumps(PRESETS[preset]));st.rerun()
 p=st.session_state.profile;p['household']=st.selectbox('Household',['Single','Couple','Family','Retired couple'],index=['Single','Couple','Family','Retired couple'].index(p['household']));p['budget']=st.selectbox('Indicative budget',['Under £500k','£500k–£750k','£750k–£1m','£1m–£2m','£2m+'],index=['Under £500k','£500k–£750k','£750k–£1m','£1m–£2m','£2m+'].index(p['budget']));p['horizon']=st.selectbox('Planning horizon',['0–3 years','3–8 years','8–15 years'],index=['0–3 years','3–8 years','8–15 years'].index(p['horizon']));p['notes']=st.text_area('Tell the app what matters',p['notes'],height=95)
 current=st.selectbox('Current location',L.name,index=int(L.index[L.name=='Marlow'][0]));st.subheader('Priorities')
 for t in THEMES:p['weights'][t]=st.slider(t,0,10,p['weights'][t],key='w'+t)
 payload={'profile':p,'current':current,'network_floor':st.session_state.network_floor,'life_network':st.session_state.network.to_dict('records')};st.download_button('Download profile JSON',json.dumps(payload,indent=2),'profile_v71.json','application/json',use_container_width=True)
 upload=st.file_uploader('Import profile JSON',type='json')
 if upload and st.button('Apply imported profile',use_container_width=True):
  x=json.load(upload);st.session_state.profile=x['profile'];st.session_state.network_floor=x.get('network_floor',58);st.session_state.network=pd.DataFrame(x.get('life_network',[]));st.rerun()
out,W=score();base=out[out.name==current].iloc[0];basehours=nrows(base)['Monthly hours'].sum();focus=sorted(p['weights'],key=p['weights'].get,reverse=True)[:3]
st.markdown(f'<div class="brief"><b>{p["household"]}, {p["budget"]}, {p["horizon"]}:</b> the profile prioritises {focus[0].lower()}, {focus[1].lower()} and {focus[2].lower()}. Places below the chosen Life Network threshold are kept explorable but excluded from the recommended shortlist.</div>',unsafe_allow_html=True)
tabs=st.tabs(['Dashboard','Recommendations','Life Network','Travel burden','Compare','Place conversation','Data quality'])
with tabs[0]:
 a,b,c,d=st.columns(4);a.metric('Catalogue',len(L));b.metric('Network nodes',len(st.session_state.network));c.metric('Current lifestyle',f"{base.Lifestyle:.0f}");d.metric('Current network',f"{base['Life Network']:.0f}")
 cs=st.columns(6)
 for i,(t,v) in enumerate(p['weights'].items()):
  with cs[i]:gauge(v*10,t,'g'+t)
with tabs[1]:
 c1,c2,c3=st.columns(3);floor=c1.slider('Minimum Life Network score',0,100,st.session_state.network_floor);st.session_state.network_floor=floor;n=c2.slider('Shortlist length',5,25,12);regions=c3.multiselect('Regions',sorted(L.region.unique()),default=sorted(L.region.unique()));candidate_pool=out[(out.name!=current)&out.region.isin(regions)&(out['Life Network']>=floor)].copy();x=candidate_pool.head(n);x['Monthly hours']=x.apply(lambda r:nrows(r)['Monthly hours'].sum(),axis=1);x['Δ hours']=x['Monthly hours']-basehours
 st.caption(f'{len(candidate_pool)} locations clear the network threshold. Suffolk and Norfolk candidates will only surface if their measured network score clears this gate.')
 st.dataframe(x[['name','county_area','region','Lifestyle','Life Network','Balanced','Monthly hours','Δ hours']].style.format({'Lifestyle':'{:.1f}','Life Network':'{:.1f}','Balanced':'{:.1f}','Monthly hours':'{:.1f}','Δ hours':'{:+.1f}'}),hide_index=True,use_container_width=True);st.scatter_chart(x,x='Lifestyle',y='Life Network',color='region',size='Balanced')
with tabs[2]:
 st.subheader('Edit, remove or add network nodes');edited=st.data_editor(st.session_state.network,num_rows='dynamic',hide_index=True,use_container_width=True,column_config={'Remove':st.column_config.CheckboxColumn('Remove',help='Tick and apply to delete this row'),'Place':st.column_config.SelectboxColumn(options=L.name.tolist()),'Category':st.column_config.SelectboxColumn(options=['Family','Friends','Home / friends','Travel','Healthcare','Culture','Other']),'Importance':st.column_config.NumberColumn(min_value=1,max_value=10),'Visits/month':st.column_config.NumberColumn(min_value=.1,max_value=30.,step=.5),'Mode':st.column_config.SelectboxColumn(options=list(MODE))})
 if st.button('Apply network changes',type='primary'):
  edited=edited[~edited.Remove.fillna(False)].copy();edited['Remove']=False;st.session_state.network=edited;st.rerun()
 cand=st.selectbox('Candidate at centre',out.name);r=out[out.name==cand].iloc[0];z=nrows(r);st.plotly_chart(radial(r,z),use_container_width=True);st.caption('The candidate is fixed at the centre. Nodes use true compass bearing and compressed mileage radius. Edge labels show miles, estimated one-way minutes and monthly return-travel burden.')
with tabs[3]:
 cand2=st.selectbox('Candidate',out.name,key='burden');r=out[out.name==cand2].iloc[0];z=nrows(r);total=z['Monthly hours'].sum();a,b,c=st.columns(3);a.metric('Monthly return travel',f'{total:.1f} h');b.metric(f'Change vs {current}',f'{total-basehours:+.1f} h');c.metric('Life Network',f"{r['Life Network']:.0f}");st.dataframe(z[['Place','Category','Mode','Importance','Visits/month','Miles','One-way minutes','Monthly hours','Node score']].style.format({'Miles':'{:.1f}','One-way minutes':'{:.0f}','Monthly hours':'{:.1f}','Node score':'{:.0f}'}),hide_index=True,use_container_width=True);st.bar_chart(z.set_index('Place')['Monthly hours']);st.warning('Journey figures are distance-based estimates at 35 mph car, 50 mph rail or 40 mph mixed, plus mode overhead. They are not live routes or timetables.')
with tabs[4]:
 choices=st.multiselect('Compare 2–4',L.name,default=['Marlow','Winchester','Stamford'],max_selections=4)
 if len(choices)>1:
  c=out[out.name.isin(choices)].set_index('name').copy();c['Monthly hours']=[nrows(r)['Monthly hours'].sum() for _,r in c.iterrows()];st.dataframe(c[['Lifestyle','Life Network','Balanced','Monthly hours','county_area','region']].T,use_container_width=True);st.bar_chart(c[['Lifestyle','Life Network','Balanced']])
with tabs[5]:
 name=st.selectbox('Discuss',out.name);r=out[out.name==name].iloc[0];drivers=sorted(K,key=lambda k:r[k]*W[k],reverse=True);hours=nrows(r)['Monthly hours'].sum();st.subheader(f"{r['name']} · {r['county_area']} · {r['region']}");st.markdown(f"For this household profile, **{LAB[drivers[0]]}**, **{LAB[drivers[1]]}** and **{LAB[drivers[2]]}** are the strongest model drivers. Lifestyle is **{r.Lifestyle:.0f}**, Life Network **{r['Life Network']:.0f}**, and estimated monthly return travel **{hours:.1f} hours**, **{hours-basehours:+.1f} hours versus {current}**.\n\n**Profile context:** {p['notes']}")
with tabs[6]:
 st.dataframe(Q,hide_index=True,use_container_width=True);st.dataframe(L[['name','county_area','region','verification_status','coordinate_precision']],hide_index=True,use_container_width=True);st.warning('Rows marked regional_seed_point need authoritative geocoding before journey decisions. The network threshold reduces recommendation pollution but does not repair a low-precision coordinate.')
